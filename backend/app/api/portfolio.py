from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.database import get_db
from app.schemas.portfolio import PositionCreate, PortfolioResponse
from app.services.portfolio import get_portfolio, add_position, remove_position
from app.utils.auth import get_current_user
from app.models.user import User

router = APIRouter()


@router.get("", response_model=PortfolioResponse)
async def portfolio(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await get_portfolio(db, current_user.id)


@router.post("", status_code=201)
async def add(
    payload: PositionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await add_position(db, current_user.id, payload)


@router.delete("/{position_id}", status_code=204)
async def remove(
    position_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await remove_position(db, current_user.id, position_id)