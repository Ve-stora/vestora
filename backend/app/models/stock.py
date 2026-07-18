from sqlalchemy import Column, String, Float, BigInteger, Date, DateTime, Enum, Index
from sqlalchemy.sql import func
import uuid
import enum

from app.database import Base, GUID


class Exchange(str, enum.Enum):
    NSE = "NSE"   # Phase 1
    USE = "USE"   # Phase 2
    DSE = "DSE"   # Phase 3
    RSE = "RSE"   # Phase 3


class StockPrice(Base):
    """Daily OHLCV data per symbol per exchange."""
    __tablename__ = "stock_prices"

    id         = Column(GUID(), primary_key=True, default=uuid.uuid4)
    symbol     = Column(String, nullable=False, index=True)
    exchange   = Column(Enum(Exchange), nullable=False, default=Exchange.NSE)
    date       = Column(Date, nullable=False, index=True)
    open       = Column(Float, nullable=True)
    high       = Column(Float, nullable=True)
    low        = Column(Float, nullable=True)
    close      = Column(Float, nullable=False)
    volume     = Column(BigInteger, nullable=True)
    market_cap = Column(Float, nullable=True)

    # Data quality flags
    data_quality_warning = Column(String, nullable=True)   # e.g. "no_trades", "low_volume"
    source               = Column(String, default="afx.kwayisi.org")
    ingested_at          = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("ix_stock_prices_symbol_date", "symbol", "date", unique=True),
    )


class StockMetadata(Base):
    """Static info per listed company."""
    __tablename__ = "stock_metadata"

    symbol      = Column(String, primary_key=True)
    exchange    = Column(Enum(Exchange), nullable=False, default=Exchange.NSE)
    name        = Column(String, nullable=False)
    sector      = Column(String, nullable=True)
    market_cap  = Column(Float, nullable=True)
    listing_date = Column(Date, nullable=True)
    updated_at  = Column(DateTime(timezone=True), server_default=func.now())