from sqlalchemy import Column, String, Boolean, DateTime, Enum
from sqlalchemy.sql import func
import uuid
import enum

from app.database import Base, GUID


class UserTier(str, enum.Enum):
    FREE = "free"
    PREMIUM = "premium"
    B2B = "b2b"          # institutional/API clients


class User(Base):
    __tablename__ = "users"

    id            = Column(GUID(), primary_key=True, default=uuid.uuid4)
    email         = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    full_name     = Column(String, nullable=True)
    tier          = Column(Enum(UserTier), default=UserTier.FREE)
    is_active     = Column(Boolean, default=True)
    created_at    = Column(DateTime(timezone=True), server_default=func.now())
    updated_at    = Column(DateTime(timezone=True), onupdate=func.now())