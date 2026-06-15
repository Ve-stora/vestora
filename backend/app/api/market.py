from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.database import get_db
from app.schemas.market import StockListResponse, StockDetailResponse, ForecastResponse, AnomalyResponse
from app.services.market import get_stocks, get_stock_detail, get_forecast, get_anomalies

router = APIRouter()

DISCLAIMER = (
   "This is market data analysis, not investment advice. "
   "Consult a licensed financial advisor before making investment decisions."
)


@router.get("/stocks", response_model=StockListResponse)
async def list_stocks(
   exchange: str = Query("NSE", description="Exchange: NSE, USE"),
   sector: Optional[str] = None,
   db: AsyncSession = Depends(get_db),
):
   """
   Returns current market data for all listed securities on the specified exchange.
   Data represents end-of-day prices from the most recent trading session.
   """
   stocks = await get_stocks(db, exchange=exchange, sector=sector)
   return {"exchange": exchange, "data": stocks, "disclaimer": DISCLAIMER}


@router.get("/stocks/{symbol}", response_model=StockDetailResponse)
async def stock_detail(
   symbol: str,
   exchange: str = Query("NSE"),
   days: int = Query(90, description="Historical lookback in days"),
   db: AsyncSession = Depends(get_db),
):
   """
   Returns historical OHLCV data, rolling statistics, and latest anomaly flags
   for a specific symbol. All values are model outputs and historical observations.
   """
   detail = await get_stock_detail(db, symbol=symbol.upper(), exchange=exchange, days=days)
   return detail


@router.get("/forecast/{symbol}", response_model=ForecastResponse)
async def forecast(
   symbol: str,
   exchange: str = Query("NSE"),
   horizon: int = Query(5, description="Forecast horizon in trading days"),
   db: AsyncSession = Depends(get_db),
):
   """
   Returns XGBoost model forecast for the specified symbol.
   Output is a model prediction based on historical data they do not imply wrongdoing or constitute advice.
   """
   flags = await get_anomalies(db, exchange=exchange, days=days)
   return {"exchange": exchange, "flags": flags, "disclaimer": DISCLAIMER}