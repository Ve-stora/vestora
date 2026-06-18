"""
Market API Router
==================
Endpoints:
  GET /api/market/stocks              — latest prices, all symbols
  GET /api/market/stocks/{symbol}     — OHLCV history + stats
  GET /api/market/forecast/{symbol}   — XGBoost forecast
  GET /api/market/anomalies           — recent anomaly flags

All responses include legal framing disclaimer.
No personalized investment advice is ever returned.
"""

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.database import get_db
from app.schemas.market import (
    StockListResponse,
    StockDetailResponse,
    ForecastResponse,
    AnomalyResponse,
)
from app.services.market import get_stocks, get_stock_detail, get_anomalies
from app.services.forecasting import run_forecast_for_symbol
from app.utils.framing import DISCLAIMER, FORECAST_DISCLAIMER, ANOMALY_DISCLAIMER

router = APIRouter()


@router.get("/stocks", response_model=StockListResponse)
async def list_stocks(
    exchange: str = Query("NSE", description="Exchange code: NSE or USE"),
    sector:   Optional[str] = Query(None, description="Filter by sector"),
    db:       AsyncSession  = Depends(get_db),
):
    """
    Returns current end-of-day market data for all listed securities.

    Data sourced from afx.kwayisi.org. Refreshed every 24 hours.
    Thin-market and no-trade days are flagged via data_quality_warning.
    """
    exchange = exchange.upper()
    if exchange not in ("NSE", "USE"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="exchange must be NSE or USE",
        )

    stocks = await get_stocks(db, exchange=exchange, sector=sector)
    return {
        "exchange":   exchange,
        "count":      len(stocks),
        "data":       stocks,
        "disclaimer": DISCLAIMER,
    }


@router.get("/stocks/{symbol}", response_model=StockDetailResponse)
async def stock_detail(
    symbol:   str,
    exchange: str = Query("NSE"),
    days:     int = Query(90, ge=5, le=1000, description="Historical lookback in days"),
    db:       AsyncSession = Depends(get_db),
):
    """
    Returns OHLCV history and rolling statistics for a specific symbol.

    All values are historical observations — not forecasts or advice.
    """
    detail = await get_stock_detail(
        db,
        symbol=symbol.upper(),
        exchange=exchange.upper(),
        days=days,
    )
    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No data found for {symbol.upper()} on {exchange.upper()}",
        )
    return detail


@router.get("/forecast/{symbol}", response_model=ForecastResponse)
async def forecast(
    symbol:   str,
    exchange: str = Query("NSE"),
    horizon:  int = Query(5, ge=1, le=20, description="Forecast horizon in trading days"),
    db:       AsyncSession = Depends(get_db),
):
    """
    Returns XGBoost directional forecast for symbol.

    Output is a model prediction based on historical price and volume data.
    It does not constitute investment advice or a recommendation to trade.
    Probability figures reflect model confidence, not guaranteed outcomes.
    """
    result = await run_forecast_for_symbol(
        db,
        symbol=symbol.upper(),
        exchange=exchange.upper(),
        horizon=horizon,
    )

    # Ensure required fields for response model
    if "error" in result and result["error"]:
        # Return a valid response shape with the error surfaced
        return {
            "symbol":              symbol.upper(),
            "exchange":            exchange.upper(),
            "forecast_date":       "",
            "horizon_days":        horizon,
            "directional_signal":  "neutral",
            "probability_up":      0.5,
            "forecast_return_pct": 0.0,
            "ci_low":              0.0,
            "ci_high":             0.0,
            "model_version":       "xgboost-v1",
            "model_accuracy":      None,
            "trained_on":          None,
            "disclaimer":          FORECAST_DISCLAIMER,
            "error":               result["error"],
        }

    return result


@router.get("/anomalies", response_model=AnomalyResponse)
async def anomalies(
    exchange: str = Query("NSE"),
    days:     int = Query(7, ge=1, le=30, description="Lookback window in days"),
    symbol:   Optional[str] = Query(None, description="Filter to specific symbol"),
    db:       AsyncSession  = Depends(get_db),
):
    """
    Returns recent Isolation Forest anomaly flags for the exchange.

    Anomalies are statistical outliers in price/volume data.
    They do not imply knowledge of any corporate event or wrongdoing.
    """
    flags = await get_anomalies(
        db,
        exchange=exchange.upper(),
        days=days,
        symbol=symbol.upper() if symbol else None,
    )
    return {
        "exchange":   exchange.upper(),
        "days":       days,
        "count":      len(flags),
        "flags":      flags,
        "disclaimer": ANOMALY_DISCLAIMER,
    }