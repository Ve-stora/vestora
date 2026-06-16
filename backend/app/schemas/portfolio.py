from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID


class PositionCreate(BaseModel):
    symbol:    str
    exchange:  str = "NSE"
    quantity:  float
    avg_price: float


class PositionResponse(BaseModel):
    id:            UUID
    symbol:        str
    exchange:      str
    quantity:      float
    avg_price:     float
    current_price: Optional[float]
    market_value:  Optional[float]
    pnl:           Optional[float]
    pnl_pct:       Optional[float]

    class Config:
        from_attributes = True


class PortfolioResponse(BaseModel):
    positions:        List[PositionResponse]
    total_value:      Optional[float]
    total_cost:       Optional[float]
    total_pnl:        Optional[float]
    total_pnl_pct:    Optional[float]
    position_count:   int