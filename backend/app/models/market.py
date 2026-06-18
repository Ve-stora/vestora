"""
Vestora Market Data Models
SQLAlchemy ORM definitions for NSE market data.
"""

from datetime import date, datetime

from sqlalchemy import (
    BigInteger, Column, Date, DateTime, Float, ForeignKey,
    Integer, String, Text, UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class Stock(Base):
    __tablename__ = "stocks"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=True)
    sector = Column(String(100), nullable=True)
    last_price = Column(Float, nullable=True)
    price_change = Column(Float, nullable=True, default=0.0)
    market_cap = Column(BigInteger, nullable=True)
    last_synced = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    prices = relationship("DailyPrice", back_populates="stock", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Stock {self.symbol} @ {self.last_price}>"


class DailyPrice(Base):
    __tablename__ = "daily_prices"

    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    open_price = Column(Float, nullable=True)
    high_price = Column(Float, nullable=True)
    low_price = Column(Float, nullable=True)
    close_price = Column(Float, nullable=False)
    volume = Column(BigInteger, nullable=True, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    stock = relationship("Stock", back_populates="prices")

    __table_args__ = (
        UniqueConstraint("stock_id", "date", name="uq_stock_date"),
    )

    def __repr__(self):
        return f"<DailyPrice {self.stock_id} {self.date} close={self.close_price}>"


class MarketIndex(Base):
    __tablename__ = "market_indices"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    value = Column(Float, nullable=True)
    change = Column(Float, nullable=True, default=0.0)
    recorded_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<MarketIndex {self.name}={self.value}>"


class Bond(Base):
    __tablename__ = "bonds"

    id = Column(Integer, primary_key=True, index=True)
    isin = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=True)
    issuer = Column(String(200), nullable=True)
    coupon_rate = Column(Float, nullable=True)
    maturity_date = Column(Date, nullable=True)
    face_value = Column(Float, nullable=True)
    last_price = Column(Float, nullable=True)
    ytm = Column(Float, nullable=True)   # Yield to Maturity
    last_synced = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Bond {self.isin} ytm={self.ytm}>"


class CorporateAction(Base):
    __tablename__ = "corporate_actions"

    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False, index=True)
    action_type = Column(String(50), nullable=False)   # DIVIDEND, SPLIT, RIGHTS, AGM
    ex_date = Column(Date, nullable=True)
    record_date = Column(Date, nullable=True)
    payment_date = Column(Date, nullable=True)
    amount = Column(Float, nullable=True)              # dividend amount or split ratio
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    stock = relationship("Stock")

    def __repr__(self):
        return f"<CorporateAction {self.action_type} stock={self.stock_id} ex={self.ex_date}>"
