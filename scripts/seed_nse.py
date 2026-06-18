"""
Seed script — populates the DB with NSE stocks and sample price data.
Run inside the backend container:
    docker compose exec backend python -m scripts.seed_nse
"""

import asyncio
from datetime import datetime, timedelta, timezone
import random

from app.core.database import AsyncSessionLocal, engine, Base
from app.models.models import Stock, StockPrice

# Top NSE equities (Phase 1 focus)
NSE_STOCKS = [
    ("SCOM", "Safaricom PLC", "Telecommunications"),
    ("EQTY", "Equity Group Holdings", "Banking"),
    ("KCB",  "KCB Group PLC", "Banking"),
    ("SCBK", "Standard Chartered Bank Kenya", "Banking"),
    ("BAT",  "British American Tobacco Kenya", "Manufacturing"),
    ("EABL", "East African Breweries", "Manufacturing"),
    ("KPLC", "Kenya Power & Lighting", "Energy"),
    ("JUB",  "Jubilee Holdings", "Insurance"),
    ("COOP", "Co-operative Bank of Kenya", "Banking"),
    ("ABSA", "ABSA Bank Kenya", "Banking"),
    ("DTK",  "Diamond Trust Bank", "Banking"),
    ("NMG",  "Nation Media Group", "Media"),
    ("KENR", "Kenya Re-Insurance", "Insurance"),
    ("PORT", "Kenya Ports Authority (Bond)", "Infrastructure"),
    ("BAMB", "Bamburi Cement", "Construction"),
]

# Approximate realistic base prices in KES
BASE_PRICES = {
    "SCOM": 18.50, "EQTY": 42.00, "KCB": 35.00, "SCBK": 185.00,
    "BAT": 430.00, "EABL": 145.00, "KPLC": 1.90, "JUB": 210.00,
    "COOP": 12.50, "ABSA": 12.00, "DTK": 62.00, "NMG": 18.00,
    "KENR": 2.20, "PORT": 95.00, "BAMB": 38.00,
}


def generate_prices(base: float, days: int = 90):
    """Simulate 90 days of OHLCV data with a random walk."""
    prices = []
    price = base
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    for i in range(days, 0, -1):
        date = today - timedelta(days=i)
        # Skip weekends (Saturday=5, Sunday=6)
        if date.weekday() >= 5:
            continue

        daily_return = random.gauss(0.0002, 0.012)
        price = max(price * (1 + daily_return), 0.10)

        high = price * (1 + abs(random.gauss(0, 0.005)))
        low  = price * (1 - abs(random.gauss(0, 0.005)))
        open_ = price * (1 + random.gauss(0, 0.003))
        volume = random.randint(50_000, 5_000_000)

        prices.append({
            "date": date,
            "open": round(open_, 2),
            "high": round(high, 2),
            "low":  round(low, 2),
            "close": round(price, 2),
            "volume": float(volume),
        })

    return prices


async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        for symbol, name, sector in NSE_STOCKS:
            # Upsert stock
            from sqlalchemy import select
            result = await session.execute(select(Stock).where(Stock.symbol == symbol))
            stock = result.scalar_one_or_none()

            if not stock:
                stock = Stock(symbol=symbol, name=name, sector=sector, exchange="NSE")
                session.add(stock)
                await session.flush()
                print(f"  Added stock: {symbol}")
            else:
                print(f"  Exists: {symbol}")

            # Check if prices already exist
            from sqlalchemy import func
            count_result = await session.execute(
                select(func.count()).where(StockPrice.stock_id == stock.id)
            )
            count = count_result.scalar()
            if count and count > 0:
                print(f"    Prices already seeded ({count} rows), skipping.")
                continue

            base = BASE_PRICES.get(symbol, 50.0)
            bars = generate_prices(base)
            for bar in bars:
                session.add(StockPrice(stock_id=stock.id, **bar))

            print(f"    Seeded {len(bars)} price bars.")

        await session.commit()
    print("\nSeed complete.")


if __name__ == "__main__":
    asyncio.run(seed())
