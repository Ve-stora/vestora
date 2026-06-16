"""
Vestora Anomaly Detection — Isolation Forest
=============================================
Per-symbol adaptive thresholds — a volume spike on Safaricom
means something different than on a low-cap USE counter.
All outputs framed as statistical observations.
"""

import pickle
import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from datetime import date, timedelta
from pathlib import Path

from app.ml.feature_engineering import add_returns, add_volume_features, add_price_gap

MODELS_DIR = Path(__file__).parent / "models"
MODELS_DIR.mkdir(exist_ok=True)

ANOMALY_FEATURE_COLS = [
    "return_zscore",
    "volume_deviation",
    "unusual_vol",
    "price_gap",
    "return_1d",
]


class VestoraAnomalyDetector:

    def __init__(self, contamination: float = 0.05):
        self.contamination = contamination
        self._models: Dict = {}

    # ── Feature prep ────────────────────────────────────────────

    def _build_anomaly_features(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy().sort_values("date").reset_index(drop=True)
        df = add_returns(df)
        df = add_volume_features(df)
        df = add_price_gap(df)

        ret_mean30 = df["return_1d"].rolling(30, min_periods=10).mean()
        ret_std30  = df["return_1d"].rolling(30, min_periods=10).std().replace(0, 1)

        df["return_zscore"]    = ((df["return_1d"] - ret_mean30) / ret_std30).fillna(0).clip(-6, 6)
        df["volume_deviation"] = df.get("vol_zscore", pd.Series(0, index=df.index))

        return df.dropna(subset=["return_zscore"])

    # ── Fit ─────────────────────────────────────────────────────

    def fit(self, symbol: str, df: pd.DataFrame) -> None:
        try:
            from sklearn.ensemble import IsolationForest
        except ImportError:
            raise RuntimeError("pip install scikit-learn")

        features = self._build_anomaly_features(df)
        cols     = [c for c in ANOMALY_FEATURE_COLS if c in features.columns]
        X        = features[cols].values

        model = IsolationForest(
            contamination=self.contamination,
            n_estimators=200,
            random_state=42,
            n_jobs=-1,
        )
        model.fit(X)

        meta = {"model": model, "feature_cols": cols, "fitted_on": date.today().isoformat()}
        self._models[symbol] = meta
        self._save(symbol, meta)

    # ── Detect ──────────────────────────────────────────────────

    def detect(self, symbol: str, df: pd.DataFrame,
               last_n_days: Optional[int] = None) -> List[Dict]:
        """
        Run anomaly detection. Returns list of flagged records.
        Optionally filter to last N days.
        """
        meta = self._load_or_get(symbol)
        if meta is None:
            return []

        features = self._build_anomaly_features(df)
        cols     = [c for c in meta["feature_cols"] if c in features.columns]
        X        = features[cols].values

        model       = meta["model"]
        preds       = model.predict(X)           # -1 anomaly, 1 normal
        raw_scores  = model.score_samples(X)     # more negative = more anomalous

        # Normalise to 0–1 (higher = more anomalous)
        s_min, s_max = raw_scores.min(), raw_scores.max()
        scores_norm  = 1 - (raw_scores - s_min) / (s_max - s_min + 1e-9)

        flags = []
        for i, (pred, score) in enumerate(zip(preds, scores_norm)):
            if pred != -1:
                continue

            row          = features.iloc[i]
            anomaly_type = self._classify(row)
            flag_date    = str(row.get("date", "")) if "date" in features.columns else ""

            if last_n_days and flag_date:
                cutoff = (date.today() - timedelta(days=last_n_days)).isoformat()
                if flag_date < cutoff:
                    continue

            flags.append({
                "symbol":        symbol,
                "exchange":      "NSE",
                "date":          flag_date,
                "anomaly_type":  anomaly_type,
                "anomaly_score": round(float(score), 3),
                "description":   self._describe(anomaly_type, row),
                "disclaimer": (
                    "Statistical anomaly — not evidence of wrongdoing or investment advice."
                ),
            })

        return sorted(flags, key=lambda x: x["anomaly_score"], reverse=True)

    def detect_latest(self, symbol: str, df: pd.DataFrame) -> Optional[Dict]:
        """Check if the most recent row is anomalous."""
        all_flags = self.detect(symbol, df, last_n_days=2)
        return all_flags[0] if all_flags else None

    # ── Helpers ──────────────────────────────────────────────────

    def _classify(self, row: pd.Series) -> str:
        if abs(row.get("volume_deviation", 0)) > 2.5:
            return "volume_spike"
        if abs(row.get("return_zscore", 0)) > 2.5:
            return "price_gap"
        if row.get("price_gap", 0) > 0.04:
            return "overnight_gap"
        return "composite"

    def _describe(self, anomaly_type: str, row: pd.Series) -> str:
        vol_dev  = abs(row.get("volume_deviation", 0))
        ret_z    = abs(row.get("return_zscore", 0))
        gap      = row.get("price_gap", 0) * 100

        return {
            "volume_spike":   f"Volume {vol_dev:.1f}σ above 30-day baseline. May indicate institutional activity or significant corporate event.",
            "price_gap":      f"Return {ret_z:.1f}σ from 30-day mean. Unusual price movement relative to recent history.",
            "overnight_gap":  f"Opening price diverged {gap:.1f}% from previous close. Overnight information event possible.",
            "composite":      "Multiple indicators deviated simultaneously from baseline.",
        }.get(anomaly_type, "Statistical anomaly detected.")

    # ── Persistence ──────────────────────────────────────────────

    def _save(self, symbol: str, meta: Dict) -> None:
        with open(MODELS_DIR / f"{symbol}_iso.pkl", "wb") as f:
            pickle.dump(meta, f)

    def _load(self, symbol: str) -> Optional[Dict]:
        path = MODELS_DIR / f"{symbol}_iso.pkl"
        if path.exists():
            with open(path, "rb") as f:
                return pickle.load(f)
        return None

    def _load_or_get(self, symbol: str) -> Optional[Dict]:
        if symbol in self._models:
            return self._models[symbol]
        meta = self._load(symbol)
        if meta:
            self._models[symbol] = meta
        return meta

    def is_fitted(self, symbol: str) -> bool:
        return self._load_or_get(symbol) is not None


detector = VestoraAnomalyDetector()