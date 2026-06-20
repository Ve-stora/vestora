"""
Vestora Pydantic Schemas
=========================
Re-export all request/response schemas for clean imports in route handlers.
"""

from app.schemas.auth import (      # noqa: F401
    UserCreate,
    UserResponse,
    Token,
    TokenData,
)

from app.schemas.market import (    # noqa: F401
    StockQuote,
    StockListResponse,
    OHLCVPoint,
    StockDetailResponse,
    ForecastResponse,
    AnomalyFlag,
    AnomalyResponse,
)

from app.schemas.portfolio import ( # noqa: F401
    PositionCreate,
    PositionResponse,
    PortfolioResponse,
)

from app.schemas.analytics import ( # noqa: F401
    AnalyticsQuery,
    AnalyticsResponse,
)

__all__ = [
    # Auth
    "UserCreate", "UserResponse", "Token", "TokenData",
    # Market
    "StockQuote", "StockListResponse", "OHLCVPoint",
    "StockDetailResponse", "ForecastResponse", "AnomalyFlag", "AnomalyResponse",
    # Portfolio
    "PositionCreate", "PositionResponse", "PortfolioResponse",
    # Analytics
    "AnalyticsQuery", "AnalyticsResponse",
]