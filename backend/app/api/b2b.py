from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.utils.auth import get_current_user, require_b2b_tier
from app.models.user import User
from app.services.market import get_stocks, get_forecast, get_anomalies

router = APIRouter()

# All B2B routes require the b2b user tier
# Brokers, SACCOs, and institutions access these endpoints under commercial license


@router.get("/market-data")
async def b2b_market_data(
    exchange: str = "NSE",
    db: AsyncSession = Depends(get_db),
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
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_b2b_tier),
):
    """
    B2B endpoint: Bulk forecast signals for all symbols.
    Returns model outputs with confidence intervals and data lineage.
    Not investment advice — data vendor output only.
    """
    # TODO: bulk forecast retrieval from Forecast table
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
    db: AsyncSession = Depends(get_db),
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