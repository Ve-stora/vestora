from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field, field_validator
from typing import List

from app.database import get_db

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


class Holding(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=10, description="Ticker symbol")
    weight: float = Field(..., gt=0, le=1.0, description="Portfolio weight (0–1)")
    exchange: str = Field("NSE", description="Exchange code: NSE or USE")

    @field_validator("symbol")
    @classmethod
    def uppercase_symbol(cls, v: str) -> str:
        return v.upper()

    @field_validator("exchange")
    @classmethod
    def uppercase_exchange(cls, v: str) -> str:
        return v.upper()


class PortfolioRequest(BaseModel):
    holdings: List[Holding] = Field(
        ...,
        min_length=1,
        max_length=50,
        description="List of holdings. Weights must sum to 1.0.",
    )

    @field_validator("holdings")
    @classmethod
    def weights_must_sum_to_one(cls, holdings: List[Holding]) -> List[Holding]:
        total = sum(h.weight for h in holdings)
        if not (0.99 <= total <= 1.01):
            raise ValueError(
                f"Holding weights must sum to 1.0, got {total:.4f}. "
                "Adjust your weights and resubmit."
            )
        return holdings


class PortfolioResponse(BaseModel):
    status: str
    holdings_count: int
    symbols: List[str]
    total_weight: float
    message: str
    disclaimer: str


@router.post(
    "/analyze",
    response_model=PortfolioResponse,
    summary="Analyze a portfolio of NSE/USE holdings",
)
async def analyze_portfolio(
    body: PortfolioRequest,
    db: AsyncSession = Depends(get_db),
):
    # TODO v0.2: wire to portfolio service
    # from app.services.portfolio import compute_portfolio_analytics
    # return await compute_portfolio_analytics(db, body.holdings)

    return PortfolioResponse(
        status="accepted",
        holdings_count=len(body.holdings),
        symbols=[h.symbol for h in body.holdings],
        total_weight=round(sum(h.weight for h in body.holdings), 4),
        message="Sharpe ratio, VaR, and correlation matrix shipping in v0.2.",
        disclaimer="Not investment advice.",
    )