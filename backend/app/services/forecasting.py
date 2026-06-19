"""
Vestora — Forecasting Service
XGBoost-based price forecasting for NSE/USE equities.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
import xgboost as xgb
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.market import StockPrice

logger = logging.getLogger(__name__)

# ── Feature engineering ───────────────────────────────────────────────────────

def _build_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build lag + rolling features for XGBoost.
    Input df must have columns: date, close, volume.
    """
    df = df.sort_values("date").copy()
    df["return_1d"] = df["close"].pct_change(1)
    df["return_5d"] = df["close"].pct_change(5)
    df["return_10d"] = df["close"].pct_change(10)
    df["vol_ma5"] = df["volume"].rolling(5).mean()
    df["vol_ma20"] = df["volume"].rolling(20).mean()
    df["price_ma5"] = df["close"].rolling(5).mean()
    df["price_ma20"] = df["close"].rolling(20).mean()
    df["volatility_10d"] = df["return_1d"].rolling(10).std()
    for lag in [1, 2, 3, 5]:
        df[f"close_lag{lag}"] = df["close"].shift(lag)
    df.dropna(inplace=True)
    return df


FEATURE_COLS = [
    "return_1d", "return_5d", "return_10d",
    "vol_ma5", "vol_ma20",
    "price_ma5", "price_ma20",
    "volatility_10d",
    "close_lag1", "close_lag2", "close_lag3", "close_lag5",
]

# ── Model ─────────────────────────────────────────────────────────────────────

def _train_model(df: pd.DataFrame) -> xgb.XGBRegressor:
    """Train a fresh XGBRegressor on available history."""
    X = df[FEATURE_COLS]
    y = df["close"].shift(-1).dropna()
    X = X.iloc[: len(y)]

    model = xgb.XGBRegressor(
        n_estimators=200,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        verbosity=0,
    )
    model.fit(X, y)
    return model


# ── DB helpers ────────────────────────────────────────────────────────────────

async def _fetch_prices(
    db: AsyncSession, symbol: str, exchange: str, lookback_days: int = 180
) -> pd.DataFrame:
    start = datetime.utcnow() - timedelta(days=lookback_days)
    stmt = (
        select(StockPrice)
        .where(
            StockPrice.symbol == symbol,
            StockPrice.exchange == exchange,
            StockPrice.date >= start,
        )
        .order_by(StockPrice.date)
    )
    result = await db.execute(stmt)
    rows = result.scalars().all()
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(
        [{"date": r.date, "close": float(r.close), "volume": float(r.volume)} for r in rows]
    )


# ── Public API ────────────────────────────────────────────────────────────────

async def run_forecast_for_symbol(
    db: AsyncSession,
    symbol: str,
    exchange: str = "NSE",
    horizon: int = 5,
) -> Dict[str, Any]:
    """
    Generate a multi-step price forecast for *symbol* on *exchange*.

    Returns
    -------
    dict with keys: symbol, exchange, last_close, forecast, confidence_interval,
                    horizon_days, model, generated_at
    """
    raw = await _fetch_prices(db, symbol, exchange)

    if raw.empty:
        raise ValueError(f"No price data found for {symbol} on {exchange}.")
    if len(raw) < 30:
        raise ValueError(
            f"Only {len(raw)} data points for {symbol} — need at least 30 to forecast."
        )

    df = _build_features(raw)

    if len(df) < 20:
        raise ValueError(f"Insufficient feature-ready rows for {symbol} after engineering.")

    model = _train_model(df)

    # Iterative multi-step forecast
    last_row = df[FEATURE_COLS].iloc[-1].copy()
    forecasts: List[float] = []

    for _ in range(horizon):
        pred = float(model.predict(last_row.values.reshape(1, -1))[0])
        forecasts.append(round(pred, 4))

        # Shift lags for next step
        for lag in [5, 3, 2, 1]:
            if f"close_lag{lag}" in last_row.index and f"close_lag{lag - 1}" in last_row.index:
                last_row[f"close_lag{lag}"] = last_row[f"close_lag{lag - 1}"]
        last_row["close_lag1"] = pred

    last_close = float(df["close"].iloc[-1])
    volatility = float(df["volatility_10d"].iloc[-1])

    # Simple symmetric confidence interval (±1 std per step)
    lower = [round(f - volatility * last_close * (i + 1) ** 0.5, 4) for i, f in enumerate(forecasts)]
    upper = [round(f + volatility * last_close * (i + 1) ** 0.5, 4) for i, f in enumerate(forecasts)]

    return {
        "symbol": symbol,
        "exchange": exchange,
        "last_close": round(last_close, 4),
        "forecast": forecasts,
        "confidence_interval": {"lower": lower, "upper": upper},
        "horizon_days": horizon,
        "model": "xgboost_v1.0",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "disclaimer": "Forecast is statistical only. Not investment advice.",
    }


async def run_batch_forecasts(
    db: AsyncSession,
    symbols: List[str],
    exchange: str = "NSE",
    horizon: int = 5,
) -> List[Dict[str, Any]]:
    """Run forecasts for multiple symbols, skipping failures gracefully."""
    results = []
    for symbol in symbols:
        try:
            result = await run_forecast_for_symbol(db, symbol, exchange, horizon)
            results.append(result)
        except ValueError as e:
            logger.warning("Skipping %s: %s", symbol, e)
            results.append({"symbol": symbol, "exchange": exchange, "error": str(e)})
        except Exception as e:
            logger.error("Unexpected error for %s: %s", symbol, e)
            results.append({"symbol": symbol, "exchange": exchange, "error": "Internal forecast error."})
    return results