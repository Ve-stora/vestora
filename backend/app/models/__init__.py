"""
Vestora ORM Models
==================
Import all models here so SQLAlchemy's metadata registry is complete
before init_db() calls Base.metadata.create_all().
"""

from app.models.user      import User, UserTier           # noqa: F401
from app.models.stock     import StockPrice, StockMetadata, Exchange  # noqa: F401
from app.models.forecast  import Forecast, AnomalyFlag, SignalDirection  # noqa: F401
from app.models.portfolio import Portfolio                # noqa: F401

# market.py models (second ORM set — core pipeline models)
from app.models.market import (  # noqa: F401
    Stock,
    DailyPrice,
    MarketIndex,
    Bond,
    CorporateAction,
)

__all__ = [
    # Auth
    "User", "UserTier",
    # Market data
    "StockPrice", "StockMetadata", "Exchange",
    "Stock", "DailyPrice", "MarketIndex", "Bond", "CorporateAction",
    # ML outputs
    "Forecast", "AnomalyFlag", "SignalDirection",
    # Portfolio
    "Portfolio",
]