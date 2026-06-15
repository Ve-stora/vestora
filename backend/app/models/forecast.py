from sqlalchemy import Column, String, Float, Integer, Date, DateTime, Enum, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
import enum

from app.database import Base


class SignalDirection(str, enum.Enum):
    BULLISH  = "bullish"
    BEARISH  = "bearish"
    NEUTRAL  = "neutral"


class Forecast(Base):
    """Stored XGBoost forecast outputs per symbol."""
    __tablename__ = "forecasts"

    id                  = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol              = Column(String, nullable=False, index=True)
    exchange            = Column(String, default="NSE")
    forecast_date       = Column(Date, nullable=False)        # date forecast was generated
    horizon_days        = Column(Integer, default=5)
    directional_signal  = Column(Enum(SignalDirection))
    forecast_return_pct = Column(Float, nullable=True)
    ci_low              = Column(Float, nullable=True)        # confidence interval low
    ci_high             = Column(Float, nullable=True)
    model_version       = Column(String, default="xgboost-v1")
    model_accuracy_30d  = Column(Float, nullable=True)        # rolling 30-day accuracy
    created_at          = Column(DateTime(timezone=True), server_default=func.now())


class AnomalyFlag(Base):
    """Isolation Forest anomaly detection outputs."""
    __tablename__ = "anomaly_flags"

    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol         = Column(String, nullable=False, index=True)
    exchange       = Column(String, default="NSE")
    date           = Column(Date, nullable=False)
    anomaly_type   = Column(String, nullable=True)    # "volume_spike", "price_gap", "bid_ask"
    anomaly_score  = Column(Float, nullable=True)     # 0-1, higher = more anomalous
    description    = Column(String, nullable=True)
    resolved       = Column(Boolean, default=False)
    created_at     = Column(DateTime(timezone=True), server_default=func.now())