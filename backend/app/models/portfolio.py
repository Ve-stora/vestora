from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Enum
from sqlalchemy.sql import func
import uuid

from app.database import Base, GUID
from app.models.stock import Exchange


class Portfolio(Base):
    __tablename__ = "portfolios"

    id         = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id    = Column(GUID(), ForeignKey("users.id", ondelete="CASCADE"),
                        nullable=False, index=True)
    symbol     = Column(String, nullable=False)
    exchange   = Column(Enum(Exchange), default=Exchange.NSE)
    quantity   = Column(Float, nullable=False)
    avg_price  = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())