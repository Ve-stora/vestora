"""
Vestora NSE Seed Data
Populates the database with real NSE stock data for development/testing.
Run once after `init_db()` to have something to forecast against.

Usage:
    python data/seeds/seed_nse.py
"""

import sys
from datetime import date, timedelta
from pathlib import Path
import random
import math

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))

from app.core.database import SessionLocal, init_db
from app.models.market import DailyPrice, MarketIndex, Stock

# Real NSE stocks with approximate June 2026 prices
NSE_STOCKS = [
    {"symbol": "SCOM",  "name": "Safaricom PLC",              "sector": "Telecommunications", "price": 18.50, "beta": 1.2},
    {"symbol": "EQTY",  "name": "Equity Group Holdings",       "sector": "Banking",            "price": 42.75, "beta": 1.1},
    {"symbol": "KCB",   "name": "KCB Group PLC",               "sector": "Banking",            "price": 38.00, "beta": 1.0},
    {"symbol": "COOP",  "name": "Co-operative Bank of Kenya",  "sector": "Banking",            "price": 13.80, "beta": 0.9},
    {"symbol": "EABL",  "name": "East African Breweries Ltd",  "sector": "Manufacturing",      "price": 135.00, "beta": 0.8},
    {"symbol": "BATK",  "name": "BAT Kenya PLC",               "sector": "Manufacturing",      "price": 390.00, "beta": 0.7},
    {"symbol": "ABSA",  "name": "ABSA Bank Kenya PLC",         "sector": "Banking",            "price": 13.90, "beta": 1.0},
    {"symbol": "NCBA",  "name": "NCBA Group PLC",              "sector": "Banking",            "price": 47.50, "beta": 0.95},
    {"symbol": "KEGN",  "name": "KenGen PLC",                  "sector": "Energy",             "price": 3.65,  "beta": 0.85},
    {"symbol": "KPLC",  "name": "Kenya Power & Lighting",      "sector": "Energy",             "price": 1.95,  "beta": 1.3},
    {"symbol": "BAMB",  "name": "Bamburi Cement PLC",          "sector": "Construction",       "price": 20.50, "beta": 0.9},
    {"symbol": "SBIC",  "name": "Stanbic Holdings Kenya",      "sector": "Banking",            "price": 95.00, "beta": 0.8},
    {"symbol": "NMG",   "name": "Nation Media Group",          "sector": "Media",              "price": 16.50, "beta": 0.75},
    {"symbol": "JUB",   "name": "Jubilee Holdings",            "sector": "Insurance",          "price": 200.00, "beta": 0.85},
    {"symbol": "KNRE",  "name": "Kenya Re-Insurance Corp",     "sector": "Insurance",          "price": 2.10,  "beta": 0.7},
    {"symbol": "TOTL",  "name": "TotalEnergies Marketing Kenya","sector": "Energy",            "price": 22.75, "beta": 0.9},
    {"symbol": "UMME",  "name": "Umeme Limited",               "sector": "Energy",             "price": 5.60,  "beta": 1.0},
    {"symbol": "SCAN",  "name": "ScanGroup PLC",               "sector": "Media",              "price": 3.25,  "beta": 0.8},
    {"symbol": "HAFR",  "name": "Home Afrika Limited",         "sector": "Real Estate",        "price": 0.38,  "beta": 1.5},
    {"symbol": "TPS",   "name": "TPS Eastern Africa (Serena)", "sector": "Tourism",            "price": 15.00, "beta": 1.1},
]

NSE_INDICES = [
    {"name": "NSE 20 Share Index",        "value": 1820.45, "change": 12.30},
    {"name": "NSE All Share Index (NASI)","value": 105.72,  "change": 0.85},
    {"name": "NSE 25 Share Index",        "value": 3241.80, "change": 18.50},
]


def generate_price_history(base_price: float, beta: float, days: int = 180) -> list[dict]:
    """
    Generate realistic-ish NSE price history using GBM + NSE-specific patterns:
    - Low base volatility (thin market = less noise, more drift)
    - Occasional illiquid sessions (zero volume)
    - Mean-reversion tendency
    """
    random.seed(42)  # reproducible
    prices = []
    price = base_price
    daily_vol = 0.012 * beta    # ~1.2% daily vol for NSE (lower than US)
    drift = 0.0002              # slight upward bias

    today = date.today()
    trading_day = today - timedelta(days=days)

    while trading_day <= today:
        if trading_day.weekday() >= 5:   # skip weekends
            trading_day += timedelta(days=1)
            continue

        # GBM price step
        shock = random.gauss(0, 1)
        ret = drift + daily_vol * shock
        # Mean reversion to base (NSE thin market effect)
        reversion = -0.02 * (price - base_price) / base_price
        ret += reversion

        price = max(price * (1 + ret), 0.05)  # floor at 5 cents

        # Volume: 30% chance of very low/zero liquidity day (NSE reality)
        base_vol = int(random.lognormvariate(12, 1.5))
        if random.random() < 0.3:
            volume = int(base_vol * random.uniform(0.01, 0.2))
        elif random.random() < 0.1:
            volume = int(base_vol * random.uniform(3, 8))   # occasional spike
        else:
            volume = base_vol

        prices.append({
            "date": trading_day,
            "close": round(price, 2),
            "volume": volume,
        })
        trading_day += timedelta(days=1)

    return prices


def seed():
    print("Initializing Vestora database...")
    init_db()
    db = SessionLocal()

    try:
        # Seed stocks + price history
        for item in NSE_STOCKS:
            stock = db.query(Stock).filter_by(symbol=item["symbol"]).first()
            if not stock:
                stock = Stock(symbol=item["symbol"])
                db.add(stock)

            from datetime import datetime
            stock.name = item["name"]
            stock.sector = item["sector"]
            stock.last_price = item["price"]
            stock.price_change = round(item["price"] * random.uniform(-0.02, 0.02), 2)
            stock.last_synced = datetime.utcnow()
            db.flush()

            # Check if history already seeded
            existing = db.query(DailyPrice).filter_by(stock_id=stock.id).count()
            if existing > 50:
                print(f"  {item['symbol']}: already has {existing} price records, skipping")
                continue

            history = generate_price_history(item["price"], item["beta"])
            for row in history:
                # Avoid dupes
                if not db.query(DailyPrice).filter_by(stock_id=stock.id, date=row["date"]).first():
                    db.add(DailyPrice(
                        stock_id=stock.id,
                        date=row["date"],
                        close_price=row["close"],
                        volume=row["volume"],
                    ))

            print(f"  {item['symbol']}: seeded {len(history)} price records")

        # Seed indices
        from datetime import datetime
        for idx_data in NSE_INDICES:
            idx = db.query(MarketIndex).filter_by(name=idx_data["name"]).first()
            if not idx:
                idx = MarketIndex(name=idx_data["name"])
                db.add(idx)
            idx.value = idx_data["value"]
            idx.change = idx_data["change"]
            idx.recorded_at = datetime.utcnow()

        db.commit()
        print(f"\n✓ Seeded {len(NSE_STOCKS)} NSE stocks with 180-day price history")
        print(f"✓ Seeded {len(NSE_INDICES)} market indices")
        print("\nNext steps:")
        print("  1. python -m ml.training.train_all --min-days 60")
        print("  2. uvicorn backend.main:app --reload")
        print("  3. GET /api/market/stocks")

    finally:
        db.close()


if __name__ == "__main__":
    seed()
