"""
Vestora Anomaly Detection Engine
Isolation Forest calibrated for thin, low-liquidity EAC equity markets.

Detects:
- Unusual price movements (pump/dump, circuit breaker events)
- Volume spikes (insider activity signals, block trades)
- Bid-ask spread anomalies
- Price-volume divergence (price moves without volume confirmation)
"""

import logging
import pickle
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import RobustScaler

logger = logging.getLogger(__name__)

MODEL_DIR = Path(__file__).parent / "saved"
MODEL_DIR.mkdir(exist_ok=True)


@dataclass
class AnomalyResult:
    symbol: str
    date: str
    is_anomaly: bool
    anomaly_score: float          # higher = more anomalous (0–1)
    anomaly_type: list[str]       # e.g. ["VOLUME_SPIKE", "PRICE_DIVERGENCE"]
    severity: str                 # LOW / MEDIUM / HIGH
    description: str
    price: float
    volume: int
    price_change_pct: float
    detected_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict:
        return self.__dict__


class NSEAnomalyDetector:
    """
    Isolation Forest anomaly detector tuned for NSE characteristics:
    - Low liquidity: many zero-volume days → volume thresholds adjusted
    - Thin float: small trades can move prices significantly
    - Infrequent trading: longer lookback windows needed
    - Regulatory gaps: real anomalies are more common than in deep markets
    """

    # NSE-specific thresholds
    CONTAMINATION = 0.04       # ~4% of trading days expected anomalous
    MIN_ROWS = 20
    VOLUME_SPIKE_MULT = 3.0    # volume > 3× 20d avg = spike
    PRICE_CIRCUIT_PCT = 0.10   # NSE ±10% single-day circuit limit

    def __init__(self, symbol: str):
        self.symbol = symbol
        self.model: Optional[IsolationForest] = None
        self.scaler = RobustScaler()
        self.feature_stats: dict = {}

    # ── Public API ─────────────────────────────────────────────────────────────

    def fit(self, df: pd.DataFrame) -> dict:
        """Train on historical data. Call once; updates periodically via scheduler."""
        df = self._prepare(df)
        if len(df) < self.MIN_ROWS:
            raise ValueError(f"Need ≥{self.MIN_ROWS} rows, got {len(df)}")

        features = self._extract_features(df)
        X = features.values
        X_scaled = self.scaler.fit_transform(X)

        self.model = IsolationForest(
            n_estimators=200,
            contamination=self.CONTAMINATION,
            max_features=0.8,
            bootstrap=True,
            random_state=42,
            n_jobs=-1,
        )
        self.model.fit(X_scaled)

        self.feature_stats = {
            "vol_mean":   float(df["volume"].mean()),
            "vol_std":    float(df["volume"].std()),
            "ret_std":    float(df["close"].pct_change().std()),
            "price_mean": float(df["close"].mean()),
        }

        self._save()
        logger.info(f"Anomaly detector fitted for {self.symbol} on {len(df)} rows")
        return {"symbol": self.symbol, "rows": len(df), "contamination": self.CONTAMINATION}

    def detect(self, df: pd.DataFrame, lookback: int = 60) -> list[AnomalyResult]:
        """
        Run anomaly detection on recent data.

        Args:
            df: Price history (min 30 rows)
            lookback: How many recent rows to evaluate

        Returns:
            List of AnomalyResult, one per trading day evaluated
        """
        if self.model is None:
            self._load()

        df = self._prepare(df).tail(lookback + 30)   # extra rows for feature calc
        features = self._extract_features(df)
        eval_features = features.tail(lookback)
        eval_df = df.tail(len(eval_features))

        X_scaled    = self.scaler.transform(eval_features.values)
        scores_raw  = self.model.decision_function(X_scaled)   # negative = more anomalous
        predictions = self.model.predict(X_scaled)              # -1 = anomaly, 1 = normal

        scores_norm = self._normalize_scores(scores_raw)

        results = []
        for i, (idx, row) in enumerate(eval_df.iterrows()):
            is_anomaly    = predictions[i] == -1
            score         = float(scores_norm[i])
            anomaly_types = self._classify_anomaly(row, df.iloc[max(0, i - 20):i])
            severity      = self._severity(score, anomaly_types)
            description   = self._describe(anomaly_types, row, df.iloc[max(0, i - 5):i])

            results.append(AnomalyResult(
                symbol=self.symbol,
                date=str(row.get("date", idx))[:10],
                is_anomaly=is_anomaly or bool(anomaly_types),
                anomaly_score=score,
                anomaly_type=anomaly_types,
                severity=severity,
                description=description,
                price=float(row["close"]),
                volume=int(row.get("volume", 0)),
                price_change_pct=round(float(row.get("ret_1d", 0)) * 100, 2),
            ))

        return results

    def detect_latest(self, df: pd.DataFrame) -> AnomalyResult:
        """Detect anomaly on the most recent trading day only."""
        return self.detect(df, lookback=1)[-1]

    # ── Feature extraction ─────────────────────────────────────────────────────

    def _extract_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Features designed to catch NSE-specific anomaly patterns.
        Shorter windows than US-market detectors (data sparsity).
        """
        f = pd.DataFrame(index=df.index)
        c = df["close"]
        v = df["volume"].replace(0, np.nan).ffill().fillna(1)   # fixed: .ffill() not fillna(method=)

        # Price return features
        f["ret_1d"]     = c.pct_change(1)
        f["ret_3d"]     = c.pct_change(3)
        f["ret_5d"]     = c.pct_change(5)
        f["abs_ret_1d"] = f["ret_1d"].abs()

        # Price deviation from rolling mean
        f["price_dev_5d"]  = (c - c.rolling(5).mean())  / c.rolling(5).std().replace(0, np.nan)
        f["price_dev_20d"] = (c - c.rolling(20).mean()) / c.rolling(20).std().replace(0, np.nan)

        # Volume features
        vol_ma_5  = v.rolling(5).mean()
        vol_ma_20 = v.rolling(20).mean()
        f["vol_ratio_5d"]  = v / vol_ma_5.replace(0, np.nan)
        f["vol_ratio_20d"] = v / vol_ma_20.replace(0, np.nan)
        f["vol_dev_20d"]   = (v - vol_ma_20) / v.rolling(20).std().replace(0, np.nan)

        # Price-volume divergence
        f["pv_divergence"] = f["ret_1d"] * (-1 * f["vol_ratio_5d"].diff())

        # Volatility clustering
        f["vol_of_vol"] = f["ret_1d"].rolling(5).std()
        f["vol_change"] = f["vol_of_vol"].pct_change()

        # High-low range
        if "high" in df.columns and "low" in df.columns:
            f["hl_range"]     = (df["high"] - df["low"]) / c
            f["hl_range_dev"] = (
                (f["hl_range"] - f["hl_range"].rolling(10).mean())
                / f["hl_range"].rolling(10).std().replace(0, np.nan)
            )
        else:
            f["hl_range"]     = f["abs_ret_1d"]
            f["hl_range_dev"] = f["price_dev_5d"]

        # Consecutive directional moves
        signs = np.sign(f["ret_1d"].fillna(0))
        f["consec_direction"] = signs.groupby((signs != signs.shift()).cumsum()).cumcount() + 1
        f["consec_direction"] *= signs

        f = f.replace([np.inf, -np.inf], np.nan).fillna(0)
        return f

    # ── Rule-based anomaly classifiers ────────────────────────────────────────

    def _classify_anomaly(self, row: pd.Series, history: pd.DataFrame) -> list[str]:
        """Layer rule-based classifiers on top of Isolation Forest."""
        types = []

        ret   = row.get("ret_1d", 0)
        vol   = row.get("volume", 0)

        if len(history) >= 5:
            avg_vol = history["volume"].mean()
            if avg_vol > 0 and vol > avg_vol * self.VOLUME_SPIKE_MULT:
                types.append("VOLUME_SPIKE")

        if abs(ret) >= 0.08:
            types.append("CIRCUIT_BREAKER_PROXIMITY")

        if ret > 0.03 and len(history) >= 5:
            avg_vol = history["volume"].mean()
            if avg_vol > 0 and vol < avg_vol * 0.5:
                types.append("PRICE_VOLUME_DIVERGENCE")

        if ret >= 0.05 and len(history) >= 5:
            avg_vol = history["volume"].mean()
            if avg_vol > 0 and vol > avg_vol * 2:
                types.append("PUMP_SIGNAL")

        if ret <= -0.05 and len(history) >= 5:
            avg_vol = history["volume"].mean()
            if avg_vol > 0 and vol > avg_vol * 2:
                types.append("DUMP_SIGNAL")

        if len(history) >= 5:
            recent_rets = history["close"].pct_change().tail(5)
            if all(recent_rets > 0):
                types.append("CONSECUTIVE_UP_5D")
            elif all(recent_rets < 0):
                types.append("CONSECUTIVE_DOWN_5D")

        return types

    def _severity(self, score: float, anomaly_types: list[str]) -> str:
        high_risk = {"PUMP_SIGNAL", "DUMP_SIGNAL", "CIRCUIT_BREAKER_PROXIMITY"}
        if any(t in high_risk for t in anomaly_types) or score > 0.75:
            return "HIGH"
        if score > 0.5 or anomaly_types:
            return "MEDIUM"
        return "LOW"

    def _describe(self, types: list[str], row: pd.Series, recent: pd.DataFrame) -> str:
        if not types:
            return "No significant anomaly detected for this trading session."

        descs = {
            "VOLUME_SPIKE":               f"Trading volume {int(row.get('volume', 0)):,} significantly exceeds 20-day average.",
            "CIRCUIT_BREAKER_PROXIMITY":  f"Single-day price movement of {row.get('ret_1d', 0)*100:.1f}% approaches NSE circuit limits.",
            "PRICE_VOLUME_DIVERGENCE":    "Price advanced on below-average volume — move may lack institutional conviction.",
            "PUMP_SIGNAL":                "Sharp price gain accompanied by elevated volume. Monitor for reversal.",
            "DUMP_SIGNAL":                "Sharp price decline with elevated volume. Possible forced selling or negative catalyst.",
            "CONSECUTIVE_UP_5D":          "Five consecutive up-days detected. Historically elevated mean-reversion risk.",
            "CONSECUTIVE_DOWN_5D":        "Five consecutive down-days detected. Watch for oversold bounce.",
        }
        return " | ".join(descs.get(t, t) for t in types)

    # ── Utilities ──────────────────────────────────────────────────────────────

    def _prepare(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").reset_index(drop=True)
        if "volume" not in df.columns:
            df["volume"] = 0
        if "ret_1d" not in df.columns:
            df["ret_1d"] = df["close"].pct_change()
        return df

    def _normalize_scores(self, raw: np.ndarray) -> np.ndarray:
        """Map decision function scores to [0, 1] where 1 = most anomalous."""
        s = -raw   # flip sign
        min_s, max_s = s.min(), s.max()
        if max_s == min_s:
            return np.zeros_like(s)
        return (s - min_s) / (max_s - min_s)

    # ── Persistence ────────────────────────────────────────────────────────────

    def _save(self):
        path = MODEL_DIR / f"{self.symbol}_anomaly.pkl"
        with open(path, "wb") as f:
            pickle.dump({
                "model":         self.model,
                "scaler":        self.scaler,
                "feature_stats": self.feature_stats,
            }, f)

    def _load(self):
        path = MODEL_DIR / f"{self.symbol}_anomaly.pkl"
        if not path.exists():
            raise FileNotFoundError(f"No anomaly model for {self.symbol} — run fit() first")
        with open(path, "rb") as f:
            state = pickle.load(f)
        self.model         = state["model"]
        self.scaler        = state["scaler"]
        self.feature_stats = state["feature_stats"]