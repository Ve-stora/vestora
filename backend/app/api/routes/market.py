"""
Vestora Market API Routes
/api/market/* — NSE stock data, forecasts, anomaly detection, market movers
"""

from datetime import datetime, timedelta
from typing import Optional

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.market import DailyPrice, MarketIndex, Stock
from app.services.nse_pipeline import NSEPipeline
from ml.models.anomaly_detector import NSEAnomalyDetector
from ml.models.forecaster import NSEForecaster

router = APIRouter(prefix="/api/market", tags=["market"])


# ── Stock listing ──────────────────────────────────────────────────────────────

@router.get("/stocks")
async def get_stocks(
    sector: Optional[str] = Query(None, description="Filter by sector"),
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """
    List NSE-listed stocks with latest prices.
    Ordered by market activity (volume × price change).
    """
    query = db.query(Stock)
    if sector:
        query = query.filter(Stock.sector.ilike(f"%{sector}%"))

    total = query.count()
    stocks = query.order_by(Stock.last_synced.desc()).offset(offset).limit(limit).all()

    return {
        "total": total,
        "stocks": [
            {
                "symbol": s.symbol,
                "name": s.name,
                "sector": s.sector,
                "last_price": s.last_price,
                "price_change": s.price_change,
                "price_change_pct": round(s.price_change / (s.last_price - s.price_change) * 100, 2)
                if s.last_price and s.price_change else 0.0,
                "last_synced": s.last_synced.isoformat() if s.last_synced else None,
            }
            for s in stocks
        ],
        "meta": {"limit": limit, "offset": offset},
    }


@router.get("/stocks/{symbol}")
async def get_stock(symbol: str, db: Session = Depends(get_db)):
    """Get single stock with latest price and 30-day history."""
    symbol = symbol.upper()
    stock = db.query(Stock).filter_by(symbol=symbol).first()
    if not stock:
        raise HTTPException(status_code=404, detail=f"Symbol {symbol} not found")

    # 30-day price history
    since = datetime.utcnow().date() - timedelta(days=30)
    prices = (
        db.query(DailyPrice)
        .filter(DailyPrice.stock_id == stock.id, DailyPrice.date >= since)
        .order_by(DailyPrice.date.asc())
        .all()
    )

    return {
        "symbol": stock.symbol,
        "name": stock.name,
        "sector": stock.sector,
        "last_price": stock.last_price,
        "price_change": stock.price_change,
        "price_change_pct": round(stock.price_change / (stock.last_price - stock.price_change) * 100, 2)
        if stock.last_price and stock.price_change else 0.0,
        "history": [
            {"date": str(p.date), "close": p.close_price, "volume": p.volume}
            for p in prices
        ],
        "last_synced": stock.last_synced.isoformat() if stock.last_synced else None,
    }


# ── Price history ──────────────────────────────────────────────────────────────

@router.get("/stocks/{symbol}/history")
async def get_price_history(
    symbol: str,
    days: int = Query(90, ge=7, le=365, description="Number of trading days"),
    db: Session = Depends(get_db),
):
    """Historical OHLCV data for a symbol."""
    symbol = symbol.upper()
    stock = db.query(Stock).filter_by(symbol=symbol).first()
    if not stock:
        raise HTTPException(status_code=404, detail=f"Symbol {symbol} not found")

    since = datetime.utcnow().date() - timedelta(days=days)
    prices = (
        db.query(DailyPrice)
        .filter(DailyPrice.stock_id == stock.id, DailyPrice.date >= since)
        .order_by(DailyPrice.date.asc())
        .all()
    )

    if not prices:
        raise HTTPException(status_code=404, detail=f"No price history for {symbol}")

    return {
        "symbol": symbol,
        "days_requested": days,
        "records": len(prices),
        "history": [
            {"date": str(p.date), "close": p.close_price, "volume": p.volume}
            for p in prices
        ],
    }


# ── Forecasting ────────────────────────────────────────────────────────────────

@router.get("/forecast/{symbol}")
async def get_forecast(
    symbol: str,
    horizon: int = Query(5, description="Forecast horizon in trading days (5 or 20)"),
    db: Session = Depends(get_db),
):
    """
    XGBoost price forecast for a symbol.
    Returns predictions + confidence intervals + directional signal.

    Model output is labeled as 'Historical patterns indicate...' in compliance
    with CMA Kenya data-vendor framing (not investment advice).
    """
    if horizon not in (5, 20):
        raise HTTPException(status_code=400, detail="horizon must be 5 or 20")

    symbol = symbol.upper()
    stock = db.query(Stock).filter_by(symbol=symbol).first()
    if not stock:
        raise HTTPException(status_code=404, detail=f"Symbol {symbol} not found")

    # Need 90+ days for reliable features
    since = datetime.utcnow().date() - timedelta(days=180)
    prices = (
        db.query(DailyPrice)
        .filter(DailyPrice.stock_id == stock.id, DailyPrice.date >= since)
        .order_by(DailyPrice.date.asc())
        .all()
    )

    if len(prices) < 30:
        raise HTTPException(
            status_code=422,
            detail=f"Insufficient price history for {symbol}. "
                   f"Need ≥30 days, have {len(prices)}.",
        )

    df = pd.DataFrame([
        {"date": str(p.date), "close": p.close_price, "volume": p.volume}
        for p in prices
    ])

    forecaster = NSEForecaster(symbol)
    try:
        result = forecaster.forecast(df, horizon=horizon)
    except FileNotFoundError:
        # Model not trained yet — train on available data
        forecaster.train(df)
        result = forecaster.forecast(df, horizon=horizon)

    response = result.to_dict()
    response["disclaimer"] = (
        f"Historical patterns indicate a {result.signal.lower()} signal over {horizon} trading days "
        f"based on a 90-day rolling model (MAPE: {result.mape:.1%}). "
        "This is model output, not investment advice."
    )
    return response


# ── Anomaly detection ──────────────────────────────────────────────────────────

@router.get("/anomalies/{symbol}")
async def get_anomalies(
    symbol: str,
    days: int = Query(30, ge=1, le=90, description="Number of recent days to scan"),
    db: Session = Depends(get_db),
):
    """
    Isolation Forest anomaly detection for recent trading sessions.
    Flags volume spikes, price-volume divergences, pump/dump signals.
    """
    symbol = symbol.upper()
    stock = db.query(Stock).filter_by(symbol=symbol).first()
    if not stock:
        raise HTTPException(status_code=404, detail=f"Symbol {symbol} not found")

    since = datetime.utcnow().date() - timedelta(days=days + 60)  # extra for feature calc
    prices = (
        db.query(DailyPrice)
        .filter(DailyPrice.stock_id == stock.id, DailyPrice.date >= since)
        .order_by(DailyPrice.date.asc())
        .all()
    )

    if len(prices) < 20:
        raise HTTPException(status_code=422, detail=f"Need ≥20 price records for {symbol}")

    df = pd.DataFrame([
        {"date": str(p.date), "close": p.close_price, "volume": p.volume}
        for p in prices
    ])

    detector = NSEAnomalyDetector(symbol)
    try:
        results = detector.detect(df, lookback=days)
    except FileNotFoundError:
        detector.fit(df)
        results = detector.detect(df, lookback=days)

    flagged = [r for r in results if r.is_anomaly]

    return {
        "symbol": symbol,
        "period_days": days,
        "total_sessions": len(results),
        "anomalies_detected": len(flagged),
        "anomaly_rate": round(len(flagged) / len(results), 3) if results else 0,
        "anomalies": [r.to_dict() for r in flagged],
        "all_sessions": [r.to_dict() for r in results],
    }


# ── Market movers ──────────────────────────────────────────────────────────────

@router.get("/movers")
async def get_market_movers(
    limit: int = Query(10, le=25),
    db: Session = Depends(get_db),
):
    """Top gainers, losers, and most active stocks today."""
    stocks = db.query(Stock).filter(Stock.last_price.isnot(None)).all()

    if not stocks:
        raise HTTPException(status_code=503, detail="Market data not yet loaded. Trigger /sync first.")

    enriched = []
    for s in stocks:
        base = s.last_price - s.price_change if s.price_change else s.last_price
        change_pct = (s.price_change / base * 100) if base and base != 0 else 0.0
        enriched.append({
            "symbol": s.symbol,
            "name": s.name,
            "sector": s.sector,
            "last_price": s.last_price,
            "price_change": s.price_change,
            "price_change_pct": round(change_pct, 2),
        })

    gainers = sorted(enriched, key=lambda x: x["price_change_pct"], reverse=True)[:limit]
    losers = sorted(enriched, key=lambda x: x["price_change_pct"])[:limit]

    return {
        "as_of": datetime.utcnow().isoformat(),
        "gainers": gainers,
        "losers": losers,
    }


# ── Market indices ─────────────────────────────────────────────────────────────

@router.get("/indices")
async def get_indices(db: Session = Depends(get_db)):
    """NSE 20 Share Index and NASI."""
    indices = db.query(MarketIndex).all()
    return {
        "indices": [
            {
                "name": idx.name,
                "value": idx.value,
                "change": idx.change,
                "recorded_at": idx.recorded_at.isoformat() if idx.recorded_at else None,
            }
            for idx in indices
        ]
    }


# ── Data sync trigger ──────────────────────────────────────────────────────────

@router.post("/sync")
async def trigger_sync(db: Session = Depends(get_db)):
    """
    Trigger a full NSE data sync.
    In production: called by APScheduler every trading day at 16:30 EAT.
    Can also be triggered manually here.
    """
    async with NSEPipeline(db) as pipeline:
        result = await pipeline.run_full_sync()
    return {"status": "ok", "result": result}
