"""
Vestora ML Training Script
Trains XGBoost forecasters + Isolation Forest anomaly detectors
for all NSE stocks with sufficient price history.

Usage:
    python -m ml.training.train_all --min-days 90
    python -m ml.training.train_all --symbol SCOM
"""

import argparse
import logging
import sys
from pathlib import Path

import pandas as pd

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.core.database import SessionLocal, init_db
from app.models.market import DailyPrice, Stock
from ml.models.anomaly_detector import NSEAnomalyDetector
from ml.models.forecaster import NSEForecaster

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("vestora.training")


def get_price_df(db, stock_id: int) -> pd.DataFrame:
    prices = (
        db.query(DailyPrice)
        .filter_by(stock_id=stock_id)
        .order_by(DailyPrice.date.asc())
        .all()
    )
    return pd.DataFrame([
        {"date": str(p.date), "close": p.close_price, "volume": p.volume or 0}
        for p in prices
    ])


def train_symbol(symbol: str, df: pd.DataFrame, force: bool = False) -> dict:
    result = {"symbol": symbol, "rows": len(df)}

    # Forecaster
    try:
        forecaster = NSEForecaster(symbol)
        train_result = forecaster.train(df)
        result["forecast"] = train_result
        logger.info(f"[{symbol}] Forecaster OK | MAPE 5d={train_result['mape_5d']:.2%}")
    except Exception as e:
        result["forecast_error"] = str(e)
        logger.warning(f"[{symbol}] Forecaster FAILED: {e}")

    # Anomaly detector
    try:
        detector = NSEAnomalyDetector(symbol)
        detector.fit(df)
        result["anomaly"] = "trained"
        logger.info(f"[{symbol}] Anomaly detector OK")
    except Exception as e:
        result["anomaly_error"] = str(e)
        logger.warning(f"[{symbol}] Anomaly detector FAILED: {e}")

    return result


def main():
    parser = argparse.ArgumentParser(description="Train Vestora ML models")
    parser.add_argument("--symbol", type=str, default=None, help="Train only this symbol")
    parser.add_argument("--min-days", type=int, default=60, help="Minimum price history days")
    parser.add_argument("--force", action="store_true", help="Retrain even if model exists")
    args = parser.parse_args()

    init_db()
    db = SessionLocal()

    try:
        if args.symbol:
            stocks = db.query(Stock).filter_by(symbol=args.symbol.upper()).all()
            if not stocks:
                logger.error(f"Symbol {args.symbol} not found in DB")
                sys.exit(1)
        else:
            stocks = db.query(Stock).all()

        logger.info(f"Training {len(stocks)} symbols (min_days={args.min_days})")

        results = {"ok": [], "skipped": [], "failed": []}

        for stock in stocks:
            df = get_price_df(db, stock.id)

            if len(df) < args.min_days:
                logger.info(f"[{stock.symbol}] Skipping — only {len(df)} days (need {args.min_days})")
                results["skipped"].append(stock.symbol)
                continue

            res = train_symbol(stock.symbol, df, force=args.force)
            if "forecast_error" in res and "anomaly_error" in res:
                results["failed"].append(stock.symbol)
            else:
                results["ok"].append(stock.symbol)

        print("\n── Training Summary ──────────────────────────")
        print(f"  Trained:  {len(results['ok'])} symbols")
        print(f"  Skipped:  {len(results['skipped'])} (insufficient history)")
        print(f"  Failed:   {len(results['failed'])}")
        if results["failed"]:
            print(f"  Failed symbols: {', '.join(results['failed'])}")
        print("─────────────────────────────────────────────\n")

    finally:
        db.close()


if __name__ == "__main__":
    main()
