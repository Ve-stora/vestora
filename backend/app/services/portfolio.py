from typing import Dict, List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from app.models.portfolio import Portfolio
from app.schemas.portfolio import PositionCreate
from app.services.market import get_stocks


async def get_portfolio(db: AsyncSession, user_id: UUID) -> Dict:
    """Fetch all positions for user, enriched with current prices."""
    result = await db.execute(
        select(Portfolio).where(Portfolio.user_id == user_id)
    )
    positions = result.scalars().all()

    if not positions:
        return {
            "positions":      [],
            "total_value":    0.0,
            "total_cost":     0.0,
            "total_pnl":      0.0,
            "total_pnl_pct":  0.0,
            "position_count": 0,
        }

    # Get current prices
    exchanges = set(p.exchange for p in positions)
    price_map: Dict[str, float] = {}
    for exchange in exchanges:
        stocks = await get_stocks(db, exchange=str(exchange))
        for s in stocks:
            price_map[s["symbol"]] = s["close"]

    enriched     = []
    total_value  = 0.0
    total_cost   = 0.0

    for p in positions:
        current = price_map.get(p.symbol)
        mkt_val = (current * p.quantity) if current else None
        cost    = p.avg_price * p.quantity
        pnl     = (mkt_val - cost) if mkt_val else None
        pnl_pct = ((pnl / cost) * 100) if (pnl is not None and cost > 0) else None

        if mkt_val:
            total_value += mkt_val
        total_cost += cost

        enriched.append({
            "id":            p.id,
            "symbol":        p.symbol,
            "exchange":      p.exchange,
            "quantity":      p.quantity,
            "avg_price":     p.avg_price,
            "current_price": current,
            "market_value":  mkt_val,
            "pnl":           round(pnl, 2) if pnl else None,
            "pnl_pct":       round(pnl_pct, 2) if pnl_pct else None,
        })

    total_pnl     = total_value - total_cost
    total_pnl_pct = (total_pnl / total_cost * 100) if total_cost > 0 else 0.0

    return {
        "positions":      enriched,
        "total_value":    round(total_value, 2),
        "total_cost":     round(total_cost, 2),
        "total_pnl":      round(total_pnl, 2),
        "total_pnl_pct":  round(total_pnl_pct, 2),
        "position_count": len(enriched),
    }


async def add_position(
    db: AsyncSession, user_id: UUID, payload: PositionCreate
) -> Portfolio:
    position = Portfolio(
        user_id   = user_id,
        symbol    = payload.symbol.upper(),
        exchange  = payload.exchange,
        quantity  = payload.quantity,
        avg_price = payload.avg_price,
    )
    db.add(position)
    await db.commit()
    await db.refresh(position)
    return position


async def remove_position(
    db: AsyncSession, user_id: UUID, position_id: UUID
) -> None:
    result = await db.execute(
        select(Portfolio).where(
            Portfolio.id      == position_id,
            Portfolio.user_id == user_id,
        )
    )
    position = result.scalar_one_or_none()
    if not position:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Position not found",
        )
    await db.delete(position)
    await db.commit()