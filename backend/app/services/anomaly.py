"""
Anomaly Detection Service
==========================
Orchestrates VestoraAnomalyDetector — fetches history, fits model,
detects anomalies, stores results to DB.

Used by:
  - API endpoint: GET /api/market/anomalies
  - Daily pipeline: run_batch_anomaly_detection()
  - B2B endpoint: GET /api/b2b/anomalies
"""

import logging
from datetime import date, timedelta
from typing import Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.ml.isolation_forest import detector
from app.models.forecast import AnomalyFlag as AnomalyFlagModel
from app.services.market import history_to_dataframe
from app.utils.framing import wrap_anomaly, ANOMALY_DISCLAIMER

logger = logging.getLogger(__name__)


# ── Per-symbol detection ─────────────────────────────────────────────────────

async def run_anomaly_detection(
    db: AsyncSession,
    symbol: str,
    exchange: str = "NSE",
    last_n_days: int = 7,
) -> List[Dict]:
    """
    Fit Isolation Forest on historical data for symbol, then detect
    anomalies in the most recent `last_n_days` trading days.

    Returns list of anomaly flag dicts (empty list if none detected).
    """
    df = await history_to_dataframe(db, symbol, exchange, days=400)

    if df.empty:
        logger.warning("No historical data for %s — skipping anomaly detection", symbol)
        return []

    if len(df) < 60:
        logger.info(
            "Insufficient history for %s (%d rows, need 60+) — skipping",
            symbol, len(df),
        )
        return []

    # Fit if not already fitted
    if not detector.is_fitted(symbol):
        try:
            detector.fit(symbol, df)
        except Exception as exc:
            logger.error("Failed to fit anomaly model for %s: %s", symbol, exc)
            return []

    # Detect recent anomalies
    try:
        flags = detector.detect(symbol, df, last_n_days=last_n_days)
    except Exception as exc:
        logger.error("Anomaly detection failed for %s: %s", symbol, exc)
        return []

    # Persist new flags to DB
    for flag in flags:
        await _store_flag(db, flag)

    # Add compliance framing to each flag
    for flag in flags:
        flag["disclaimer"] = ANOMALY_DISCLAIMER

    return flags


# ── Batch orchestration ──────────────────────────────────────────────────────

async def run_batch_anomaly_detection(
    db: AsyncSession,
    symbols: List[str],
    exchange: str = "NSE",
    last_n_days: int = 3,
) -> Dict:
    """
    Run anomaly detection for a list of symbols.
    Used by the daily data pipeline to sweep the full exchange.

    Returns summary dict with all flags aggregated.
    """
    all_flags: List[Dict] = []
    failed:    List[str]  = []

    for symbol in symbols:
        try:
            flags = await run_anomaly_detection(
                db, symbol, exchange, last_n_days=last_n_days
            )
            all_flags.extend(flags)
        except Exception as exc:
            logger.error("Batch anomaly failed for %s: %s", symbol, exc)
            failed.append(symbol)

    result = {
        "total_flags": len(all_flags),
        "exchange":    exchange,
        "flags":       all_flags,
        "processed":   len(symbols),
        "failed":      failed,
        "disclaimer":  ANOMALY_DISCLAIMER,
    }

    logger.info(
        "Batch anomaly complete — %d symbols, %d flags, %d failed",
        len(symbols), len(all_flags), len(failed),
    )
    return result


# ── DB query helpers ─────────────────────────────────────────────────────────

async def get_recent_anomalies(
    db: AsyncSession,
    exchange: str = "NSE",
    days: int = 7,
    symbol: Optional[str] = None,
) -> List[Dict]:
    """
    Retrieve stored anomaly flags from DB for the last `days` days.
    Optionally filtered by symbol.
    """
    since = date.today() - timedelta(days=days)

    query = (
        select(AnomalyFlagModel)
        .where(
            AnomalyFlagModel.exchange == exchange,
            AnomalyFlagModel.date     >= since,
        )
        .order_by(desc(AnomalyFlagModel.date), desc(AnomalyFlagModel.anomaly_score))
    )

    if symbol:
        query = query.where(AnomalyFlagModel.symbol == symbol.upper())

    result = await db.execute(query)
    rows   = result.scalars().all()

    return [
        {
            "symbol":        row.symbol,
            "exchange":      row.exchange,
            "date":          str(row.date),
            "anomaly_type":  row.anomaly_type,
            "anomaly_score": row.anomaly_score,
            "description":   row.description,
            "disclaimer":    ANOMALY_DISCLAIMER,
        }
        for row in rows
    ]


# ── Persistence ──────────────────────────────────────────────────────────────

async def _store_flag(db: AsyncSession, flag: Dict) -> None:
    """Persist anomaly flag to DB. Skip exact duplicates (symbol+date+type)."""
    existing = await db.execute(
        select(AnomalyFlagModel).where(
            AnomalyFlagModel.symbol       == flag["symbol"],
            AnomalyFlagModel.date         == flag.get("date"),
            AnomalyFlagModel.anomaly_type == flag.get("anomaly_type"),
        )
    )
    if existing.scalar_one_or_none():
        return  # already stored — idempotent

    try:
        row = AnomalyFlagModel(
            symbol        = flag["symbol"],
            exchange      = flag.get("exchange", "NSE"),
            date          = flag.get("date"),
            anomaly_type  = flag.get("anomaly_type"),
            anomaly_score = flag.get("anomaly_score", 0.0),
            description   = flag.get("description", ""),
        )
        db.add(row)
        await db.commit()
        logger.debug("Stored anomaly flag: %s %s", flag["symbol"], flag.get("anomaly_type"))
    except Exception as exc:
        await db.rollback()
        logger.error("Failed to store anomaly flag for %s: %s", flag.get("symbol"), exc)