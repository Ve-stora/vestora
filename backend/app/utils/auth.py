from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User, UserTier
from app.services.auth import decode_token, get_user_by_id

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_token(token)
    if payload is None:
        raise credentials_exc

    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exc

    user = await get_user_by_id(db, user_id)
    if user is None or not user.is_active:
        raise credentials_exc

    return user


async def require_premium(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.tier not in (UserTier.PREMIUM, UserTier.B2B):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Premium subscription required",
        )
    return current_user


async def require_b2b_tier(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.tier != UserTier.B2B:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="B2B license required. Contact veritasndiema@gmail.com",
        )
    return current_user