"""
Vestora DB Seed Script
=======================
Populates StockMetadata from data/seeds/nse_symbols.json.
Safe to run multiple times (upserts on symbol PK).

Usage:
    python -m app.db_seed
    # or via run.sh: bash run.sh seed
"""

import json
import logging
import os
import sys
from pathlib import Path

from sqlalchemy.orm import Session

from app.database import SessionLocal, init_db
from app.models.stock import StockMetadata, Exchange

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger("vestora.seed")

SEED_FILE = Path(__file__).parents[3] / "data" / "seeds" / "nse_symbols.json"


def seed_nse_symbols(db: Session) -> int:
    """Insert or update NSE stock metadata from seed file. Returns count upserted."""
    if not SEED_FILE.exists():
        logger.error("Seed file not found: %s", SEED_FILE)
        return 0

    with open(SEED_FILE) as f:
        payload = json.load(f)

    symbols = payload.get("symbols", [])
    upserted = 0

    for item in symbols:
        existing = db.get(StockMetadata, item["symbol"])
        if existing:
            existing.name   = item.get("name", existing.name)
            existing.sector = item.get("sector", existing.sector)
        else:
            record = StockMetadata(
                symbol   = item["symbol"],
                exchange = Exchange.NSE,
                name     = item.get("name", item["symbol"]),
                sector   = item.get("sector"),
            )
            db.add(record)
        upserted += 1

    db.commit()
    logger.info("Seeded %d NSE symbols into stock_metadata", upserted)
    return upserted


def seed_market_indices(db: Session) -> None:
    """Seed baseline NSE index names so the indices table is not empty."""
    from app.models.market import MarketIndex

    indices = [
        MarketIndex(name="NSE 20 Share Index", value=None, change=None),
        MarketIndex(name="NASI",               value=None, change=None),
        MarketIndex(name="NSE 25 Share Index", value=None, change=None),
    ]
    for idx in indices:
        existing = db.query(MarketIndex).filter_by(name=idx.name).first()
        if not existing:
            db.add(idx)

    db.commit()
    logger.info("Market index stubs ready")


def run():
    logger.info("Initialising database…")
    init_db()

    db = SessionLocal()
    try:
        seed_nse_symbols(db)
        seed_market_indices(db)
        logger.info("Seed complete.")
    except Exception as e:
        logger.error("Seed failed: %s", e)
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    run()