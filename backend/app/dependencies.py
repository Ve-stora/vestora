"""
Vestora FastAPI Dependencies
============================
Centralises reusable Depends() callables.
Import from here rather than from individual service modules.

NOTE: The DB session is SYNCHRONOUS (standard SQLAlchemy).
      The type hint uses Session (not AsyncSession).
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User, UserTier
from app.services.auth import decode_token, get_user_by_id

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Validate JWT and return the authenticated User. Raises 401 on failure."""
    exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_token(token)
    if payload is None:
        raise exc
    user_id: str | None = payload.get("sub")
    if not user_id:
        raise exc
    user = get_user_by_id(db, user_id)
    if user is None or not user.is_active:
        raise exc
    return user


def require_premium(current_user: User = Depends(get_current_user)) -> User:
    """Require PREMIUM or B2B tier."""
    if current_user.tier not in (UserTier.PREMIUM, UserTier.B2B):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Premium subscription required",
        )
    return current_user


def require_b2b(current_user: User = Depends(get_current_user)) -> User:
    """Require B2B tier — institutional/API clients only."""
    if current_user.tier != UserTier.B2B:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="B2B API license required. Contact veritasndiema@gmail.com",
        )
    return current_user


# Re-export get_db for convenience
__all__ = ["get_db", "get_current_user", "require_premium", "require_b2b"]