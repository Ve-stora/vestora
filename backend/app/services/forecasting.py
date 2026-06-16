"""
Forecasting Service
====================
Orchestrates VestoraForecaster — fetches data, runs model, stores results.
"""

import json
from datetime import date
from typing import Dict, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.ml.xgboost_model import forecaster
from app.models.forecast import Forecast, SignalDirection
from app.services.market import history_to_dataframe
from app.utils.framing import wrap_forecast


async def run_forecast_for_symbol(
    db: AsyncSession,
    symbol: str,
    exchange: str = "NSE",
    horizon: int = 5,
) -> Dict:
    """
    On-demand forecast for a single symbol.
    Trains model if not already trained, then predicts and stores result.
    """
    df = await history_to_dataframe(db, symbol, exchange, days=400)

    if df.empty:
        return {
            "symbol":   symbol,
            "exchange": exchange,
            "error":    f"No historical data for {symbol}",
            "disclaimer": "Not investment advice.",
        }

    # Train if needed
    if not forecaster.is_trained(symbol):
        train_result = forecaster.train(symbol, df)
        if "error" in train_result:
            return {**train_result, "disclaimer": "Not investment advice."}

    result = forecaster.predict(symbol, df)

    if "error" not in result:
        await _store_forecast(db, result)

    return wrap_forecast(result)


async def run_batch_forecasts(
    db: AsyncSession,
    symbols: List[str],
    exchange: str = "NSE",
    horizon: int = 5,
) -> List[Dict]:
    """Run forecasts for a list of symbols. Used by daily pipeline."""
    results = []
    for symbol in symbols:
        result = await run_forecast_for_symbol(db, symbol, exchange, horizon)
        results.append(result)
    return results


async def _store_forecast(db: AsyncSession, result: Dict) -> None:
    """Persist forecast to DB."""
    direction_map = {
        "bullish": SignalDirection.BULLISH,
        "bearish": SignalDirection.BEARISH,
        "neutral": SignalDirection.NEUTRAL,
    }

    row = Forecast(
        symbol             = result["symbol"],
        exchange           = result.get("exchange", "NSE"),
        forecast_date      = date.today(),
        horizon_days       = result.get("horizon_days", 5),
        directional_signal = direction_map.get(
            result.get("directional_signal", "neutral"), SignalDirection.NEUTRAL
        ),
        forecast_return_pct = result.get("forecast_return_pct"),
        ci_low              = result.get("ci_low"),
        ci_high             = result.get("ci_high"),
        model_version       = result.get("model_version", "xgboost-v1"),
        model_accuracy_30d  = result.get("model_accuracy"),
    )
    db.add(row)
    await db.commit()