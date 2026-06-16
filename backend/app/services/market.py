"""
Market Service
==============
Cache-first data layer. On cache miss: scrape → validate → store → return.
Cache TTL matches data freshness — NSE data is end-of-day so 24hr TTL is correct.
"""

import pandas as pd
from typing import List, Optional, Dict
from datetime import date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.models.stock import StockPrice, StockMetadata, Exchange
from app.models.forecast import Forecast, AnomalyFlag
from app.services.scraper import scraper
from app.utils.cache import cache_get, cache_set
from app.config import settings


# ── Stocks ───────────────────────────────────────────────────

async def get_stocks(
    db: AsyncSession,
    exchange: str = "NSE",
    sector: Optional[str] = None,
) -> List[Dict]:
    """
    Returns latest price for all symbols on exchange.
    Cache first (24hr TTL), scraper on miss.
    """
    cache_key = f"stocks:{exchange}:{sector or 'all'}"
    cached    = await cache_get(cache_key)
    if cached:
        return cached

    # Try DB first — latest close per symbol
    subq = (
        select(StockPrice.symbol, StockPrice.date)
        .where(StockPrice.exchange == exchange)
        .group_by(StockPrice.symbol)
        .having(StockPrice.date == select(StockPrice.date)
                .where(StockPrice.exchange == exchange)
                .order_by(desc(StockPrice.date))
                .limit(1)
                .scalar_subquery())
    )
    result = await db.execute(
        select(StockPrice, StockMetadata)
        .join(StockMetadata, StockMetadata.symbol == StockPrice.symbol, isouter=True)
        .where(StockPrice.exchange == exchange)
        .order_by(desc(StockPrice.date))
    )
    rows = result.all()

    if not rows:
        # DB empty — scrape live
        raw  = await scraper.fetch_nse_stocks() if exchange == "NSE" else await scraper.fetch_use_stocks()
        data = scraper.validate(raw)
        await cache_set(cache_key, data, settings.MARKET_DATA_TTL)
        return data

    seen  = set()
    data  = []
    for price_row, meta_row in rows:
        if price_row.symbol in seen:
            continue
        seen.add(price_row.symbol)
        if sector and meta_row and meta_row.sector != sector:
            continue
        data.append({
            "symbol":               price_row.symbol,
            "name":                 meta_row.name if meta_row else price_row.symbol,
            "exchange":             exchange,
            "close":                price_row.close,
            "volume":               price_row.volume,
            "date":                 str(price_row.date),
            "sector":               meta_row.sector if meta_row else None,
            "data_quality_warning": price_row.data_quality_warning,
            "source":               price_row.source,
            "change_pct":           None,   # computed below if prev day in DB
        })

    await cache_set(cache_key, data, settings.MARKET_DATA_TTL)
    return data


async def get_stock_detail(
    db: AsyncSession,
    symbol: str,
    exchange: str = "NSE",
    days: int = 90,
) -> Dict:
    """Historical OHLCV for a symbol over the last N days."""
    cache_key = f"detail:{exchange}:{symbol}:{days}"
    cached    = await cache_get(cache_key)
    if cached:
        return cached

    since  = date.today() - timedelta(days=days)
    result = await db.execute(
        select(StockPrice)
        .where(
            StockPrice.symbol   == symbol,
            StockPrice.exchange == exchange,
            StockPrice.date     >= since,
        )
        .order_by(StockPrice.date)
    )
    rows = result.scalars().all()

    history = [
        {
            "date":   str(r.date),
            "open":   r.open,
            "high":   r.high,
            "low":    r.low,
            "close":  r.close,
            "volume": r.volume,
        }
        for r in rows
    ]

    data = {"symbol": symbol, "exchange": exchange, "history": history, "days": days}
    await cache_set(cache_key, data, settings.ANALYTICS_CACHE_TTL)
    return data


# ── Forecasts ────────────────────────────────────────────────

async def get_forecast(
    db: AsyncSession,
    symbol: str,
    exchange: str = "NSE",
    horizon: int = 5,
) -> Dict:
    """
    Return latest stored forecast or trigger on-demand.
    Cached for 1hr — forecasts don't change intraday.
    """
    cache_key = f"forecast:{exchange}:{symbol}:{horizon}"
    cached    = await cache_get(cache_key)
    if cached:
        return cached

    # Check DB for today's forecast
    result = await db.execute(
        select(Forecast)
        .where(
            Forecast.symbol       == symbol,
            Forecast.exchange     == exchange,
            Forecast.forecast_date == date.today(),
            Forecast.horizon_days  == horizon,
        )
        .order_by(desc(Forecast.created_at))
        .limit(1)
    )
    row = result.scalar_one_or_none()

    if row:
        data = {
            "symbol":              row.symbol,
            "exchange":            row.exchange,
            "forecast_date":       str(row.forecast_date),
            "horizon_days":        row.horizon_days,
            "directional_signal":  row.directional_signal,
            "probability_up":      None,
            "forecast_return_pct": None,
            "ci_low":              row.ci_low,
            "ci_high":             row.ci_high,
            "model_version":       row.model_version,
            "model_accuracy":      row.model_accuracy_30d,
            "trained_on":          None,
            "disclaimer": (
                "Model forecast based on historical data. Not investment advice."
            ),
        }
        await cache_set(cache_key, data, settings.ANALYTICS_CACHE_TTL)
        return data

    # No stored forecast — run on-demand
    from app.services.forecasting import run_forecast_for_symbol
    data = await run_forecast_for_symbol(db, symbol, exchange, horizon)
    await cache_set(cache_key, data, settings.ANALYTICS_CACHE_TTL)
    return data


# ── Anomalies ────────────────────────────────────────────────

async def get_anomalies(
    db: AsyncSession,
    exchange: str = "NSE",
    days: int = 7,
) -> List[Dict]:
    cache_key = f"anomalies:{exchange}:{days}"
    cached    = await cache_get(cache_key)
    if cached:
        return cached

    since  = date.today() - timedelta(days=days)
    result = await db.execute(
        select(AnomalyFlag)
        .where(
            AnomalyFlag.exchange == exchange,
            AnomalyFlag.date     >= since,
        )
        .order_by(desc(AnomalyFlag.created_at))
    )
    rows = result.scalars().all()

    data = [
        {
            "symbol":        r.symbol,
            "exchange":      r.exchange,
            "date":          str(r.date),
            "anomaly_type":  r.anomaly_type,
            "anomaly_score": r.anomaly_score,
            "description":   r.description,
            "disclaimer":    "Statistical anomaly only — not investment advice.",
        }
        for r in rows
    ]

    await cache_set(cache_key, data, settings.ANALYTICS_CACHE_TTL)
    return data


# ── Helpers ──────────────────────────────────────────────────

async def history_to_dataframe(
    db: AsyncSession, symbol: str, exchange: str = "NSE", days: int = 400
) -> pd.DataFrame:
    """Load historical data for a symbol as a DataFrame — used by ML services."""
    detail = await get_stock_detail(db, symbol, exchange, days)
    if not detail.get("history"):
        return pd.DataFrame()
    return pd.DataFrame(detail["history"])