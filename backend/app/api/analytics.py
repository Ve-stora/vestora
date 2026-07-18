from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_db
from app.schemas.analytics import AnalyticsQuery, AnalyticsResponse
from app.services.analytics import run_analytics_query
from app.utils.auth import get_current_user
from app.models.user import User

router = APIRouter()

# System prompt enforcing data-vendor posture (never advisory)
ANALYTICS_SYSTEM_PROMPT = """
You are Vestora's market analytics engine for East African capital markets.
You analyze NSE (Nairobi Securities Exchange) and EAC market data and provide
data-driven insights.

STRICT RULES:
1. Never tell users to buy, sell, or hold any security.
2. Never provide personalized investment advice.
3. Always frame outputs as data observations:
   - "The data shows..."
   - "Historically, this pattern..."
   - "The model indicates..."
   - "Market data suggests..."
4. Always append: "This is market data analysis, not investment advice."
5. When asked for a recommendation, redirect:
   "I can show you what the data indicates, but investment decisions
    should be made with a licensed advisor who understands your full
    financial situation."
6. Cite data sources and timestamps for all factual claims.
7. You cover NSE primarily. Phase 2 will add USE (Uganda).
"""


@router.post("/analytics", response_model=AnalyticsResponse)
async def analytics_query(
    payload: AnalyticsQuery,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    """
    Natural language analytics query engine.
    Returns data observations and model outputs — not investment advice.
    """
    result = await run_analytics_query(
        query=payload.query,
        context=payload.context,
        system_prompt=ANALYTICS_SYSTEM_PROMPT,
        db=db,
    )
    return result