"""
B2B API Routes
===============
Mounted at /api/b2b/* by app/api/__init__.py.
All endpoints require B2B tier — institutional/broker clients only.

  GET /api/b2b/market-data   — full exchange data with lineage metadata
  GET /api/b2b/forecasts     — bulk forecast signals
  GET /api/b2b/anomalies     — anomaly flags with scoring metadata
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_db
from app.utils.auth import require_b2b_tier
from app.models.user import User
from app.services.market import get_stocks, get_anomalies

router = APIRouter()


@router.get("/market-data")
async def b2b_market_data(
    exchange: str = "NSE",
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_b2b_tier),
):
    """
    B2B endpoint: Full exchange market data with data lineage metadata.
    Rate limit: per commercial license agreement.
    """
    stocks = await get_stocks(db, exchange=exchange)
    return {
        "exchange": exchange,
        "data": stocks,
        "data_lineage": {
            "source": "afx.kwayisi.org",
            "exchange": exchange,
            "latency": "end-of-day",
            "license": "commercial",
        },
    }


@router.get("/forecasts")
async def b2b_forecasts(
    exchange: str = "NSE",
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_b2b_tier),
):
    """
    B2B endpoint: Bulk forecast signals for all symbols.
    Returns model outputs with confidence intervals and data lineage.
    Not investment advice — data vendor output only.
    """
    # TODO v0.2: bulk forecast retrieval from Forecast table
    return {
        "exchange": exchange,
        "forecasts": [],
        "model": "xgboost-v1",
        "disclaimer": "Model outputs only. Not investment advice.",
    }


@router.get("/anomalies")
async def b2b_anomalies(
    exchange: str = "NSE",
    days: int = 7,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_b2b_tier),
):
    """
    B2B endpoint: Anomaly flags with full scoring metadata.
    """
    flags = await get_anomalies(db, exchange=exchange, days=days)
    return {
        "exchange": exchange,
        "flags": flags,
        "model": "isolation-forest-v1",
        "disclaimer": "Statistical anomaly detection. Not investment advice.",
    }