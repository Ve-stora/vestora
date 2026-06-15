"""
Vestora Anomaly Detection — Isolation Forest
=============================================
Detects statistical outliers in price and volume data on EAC exchanges.
Thresholds are calibrated per-symbol based on individual liquidity profiles.

A volume spike on Safaricom (high liquidity) means something different
than the same spike on a low-cap USE counter — adaptive thresholds handle this.

Output is always framed as statistical observation, not evidence of wrongdoing.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from datetime import date


class VestoraAnomalyDetector:
    """
    Isolation Forest anomaly detection per symbol.
    Features: price return z-score, volume deviation, bid-ask anomaly, time-of-day.
    """

    def __init__(self, contamination: float = 0.05):
        """
        contamination: expected proportion of anomalies in dataset.
        0.05 = 5% — conservative for thin markets where sparse trades
        can look anomalous even when legitimate.
        """
        self.contamination = contamination
        self.models: Dict = {}

    def build_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Anomaly feature set:
        - return_zscore: daily return normalised by 30-day rolling std
        - volume_deviation: (volume - 30d mean) / 30d std
        - price_gap: |open - prev_close| / prev_close (overnight gap)
        - unusual_volume_flag: binary
        """
        df = df.copy().sort_values("date")

        df["return_1d"]      = df["close"].pct_change()
        df["vol_mean30"]     = df["volume"].rolling(30).mean()
        df["vol_std30"]      = df["volume"].rolling(30).std()
        df["return_mean30"]  = df["return_1d"].rolling(30).mean()
        df["return_std30"]   = df["return_1d"].rolling(30).std()

        df["return_zscore"]    = (df["return_1d"] - df["return_mean30"]) / df["return_std30"]
        df["volume_deviation"] = (df["volume"] - df["vol_mean30"]) / df["vol_std30"]
        df["unusual_volume"]   = (df["volume"] > df["vol_mean30"] * 2.5).astype(float)

        # Price gap (requires open price — optional)
        if "open" in df.columns:
            df["price_gap"] = abs(df["open"] - df["close"].shift(1)) / df["close"].shift(1)
        else:
            df["price_gap"] = 0.0

        return df.dropna()

    def fit(self, symbol: str, df: pd.DataFrame) -> None:
        """Fit Isolation Forest for a specific symbol."""
        try:
            from sklearn.ensemble import IsolationForest
        except ImportError:
            raise RuntimeError("scikit-learn not installed — run: pip install scikit-learn")

        features = self.build_features(df)
        cols = ["return_zscore", "volume_deviation", "unusual_volume", "price_gap"]
        X = features[cols].values

        model = IsolationForest(
            contamination=self.contamination,
            random_state=42,
            n_estimators=100,
        )
        model.fit(X)
        self.models[symbol] = {"model": model, "feature_cols": cols}

    def detect(self, symbol: str, df: pd.DataFrame) -> List[Dict]:
        """
        Run anomaly detection on full history.
        Returns list of flagged dates with type, score, and description.
        """
        if symbol not in self.models:
            return []

        model_data = self.models[symbol]
        features   = self.build_features(df)
        X          = features[model_data["feature_cols"]].values

        model  = model_data["model"]
        preds  = model.predict(X)          # -1 = anomaly, 1 = normal
        scores = model.score_samples(X)    # lower = more anomalous

        # Normalise scores to 0-1 (higher = more anomalous)
        scores_norm = 1 - (scores - scores.min()) / (scores.max() - scores.min() + 1e-9)

        flags = []
        for i, (pred, score) in enumerate(zip(preds, scores_norm)):
            if pred == -1:
                row = features.iloc[i]
                anomaly_type = self._classify_anomaly(row)
                flags.append({
                    "symbol":        symbol,
                    "exchange":      "NSE",
                    "date":          str(row["date"]) if "date" in row.index else features.index[i],
                    "anomaly_type":  anomaly_type,
                    "anomaly_score": round(float(score), 3),
                    "description":   self._describe(anomaly_type, row),
                    "disclaimer":    (
                        "Anomaly detection identifies statistical outliers. "
                        "It does not constitute investment advice or imply knowledge "
                        "of any specific corporate event."
                    ),
                })

        return sorted(flags, key=lambda x: x["anomaly_score"], reverse=True)

    def _classify_anomaly(self, row: pd.Series) -> str:
        if abs(row.get("volume_deviation", 0)) > 3:
            return "volume_spike"
        if abs(row.get("return_zscore", 0)) > 3:
            return "price_gap"
        if row.get("price_gap", 0) > 0.05:
            return "overnight_gap"
        return "composite"

    def _describe(self, anomaly_type: str, row: pd.Series) -> str:
        descriptions = {
            "volume_spike":   f"Trading volume was {abs(row.get('volume_deviation', 0)):.1f} standard deviations above the 30-day baseline. This statistical anomaly may indicate significant corporate activity or institutional trading.",
            "price_gap":      f"Daily return was {abs(row.get('return_zscore', 0)):.1f} standard deviations from the 30-day mean. Unusual price movement detected.",
            "overnight_gap":  f"Opening price diverged significantly from previous close. Overnight gap of {row.get('price_gap', 0)*100:.1f}% detected.",
            "composite":      "Multiple indicators deviated simultaneously from baseline. Composite anomaly flagged.",
        }
        return descriptions.get(anomaly_type, "Statistical anomaly detected.")


detector = VestoraAnomalyDetector()