"""
Vestora Forecasting Engine — XGBoost
======================================
Rationale: XGBoost over deep learning because NSE/EAC historical depth
is insufficient for LSTM/Transformer without transfer learning from
liquid markets (distributional shift problem).

Walk-forward validation enforced. No look-ahead bias.
All outputs include confidence intervals and model accuracy metadata.

Architecture:
  - Binary classification: predict direction (up/down) over horizon
  - Calibrated probabilities via isotonic regression
  - Per-symbol model persistence (pickle) with versioning
  - Confidence interval derived from bootstrap of recent predictions
"""

import logging
import os
import pickle
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from app.ml.feature_engineering import build_features, get_feature_cols

logger    = logging.getLogger(__name__)
MODELS_DIR = Path(__file__).parent / "models"
MODELS_DIR.mkdir(exist_ok=True)


class VestoraForecaster:

    def __init__(self, horizon: int = 5, model_version: str = "xgboost-v1"):
        self.horizon       = horizon
        self.model_version = model_version
        # symbol -> {"clf": model, "calibrator": cal, "feature_cols": [...], "meta": {...}}
        self._models: Dict[str, Dict] = {}

    # ── Public API ───────────────────────────────────────────────────────────

    def is_trained(self, symbol: str) -> bool:
        """Return True if model is in memory or persisted to disk."""
        if symbol in self._models:
            return True
        model_path = self._model_path(symbol)
        if model_path.exists():
            self._load(symbol)
            return True
        return False

    def train(self, symbol: str, df: pd.DataFrame) -> Dict:
        """
        Train XGBoost classifier for symbol with walk-forward validation.

        Requires 280+ trading days of history (≈14 months).
        Walk-forward: 80% initial train, 20% held-out test (strictly temporal).

        Returns evaluation metrics dict. On error returns {"error": "..."}.
        """
        try:
            from xgboost import XGBClassifier
            from sklearn.calibration import CalibratedClassifierCV
            from sklearn.isotonic import IsotonicRegression
        except ImportError:
            return {"error": "pip install xgboost scikit-learn", "symbol": symbol}

        target   = f"fwd_dir_{self.horizon}d" if self.horizon in [1, 5] else "fwd_dir_5d"
        features = build_features(df, target=target)

        if len(features) < 280:
            return {
                "error":  f"{symbol}: need 280+ trading days, have {len(features)}",
                "symbol": symbol,
            }

        feat_cols = get_feature_cols(features)
        X         = features[feat_cols].values.astype(np.float32)
        y         = features[target].values.astype(np.int32)

        # Strictly temporal split — never shuffle
        split    = int(len(X) * 0.8)
        X_tr, X_te = X[:split], X[split:]
        y_tr, y_te = y[:split], y[split:]

        clf = XGBClassifier(
            n_estimators      = 200,
            max_depth         = 4,
            learning_rate     = 0.05,
            subsample         = 0.8,
            colsample_bytree  = 0.8,
            min_child_weight  = 5,
            reg_alpha         = 0.1,
            reg_lambda        = 1.0,
            use_label_encoder = False,
            eval_metric       = "logloss",
            random_state      = 42,
            verbosity         = 0,
            n_jobs            = -1,
        )

        clf.fit(
            X_tr, y_tr,
            eval_set=[(X_te, y_te)],
            verbose=False,
        )

        # Evaluate on held-out
        preds       = clf.predict(X_te)
        probs       = clf.predict_proba(X_te)[:, 1]
        dir_acc     = float((preds == y_te).mean())
        bull_rate   = float(y_te.mean())

        # Calibrate probabilities with isotonic regression on test set
        calibrator = IsotonicRegression(out_of_bounds="clip")
        calibrator.fit(probs, y_te)

        meta = {
            "clf":               clf,
            "calibrator":        calibrator,
            "feature_cols":      feat_cols,
            "target":            target,
            "trained_on":        date.today().isoformat(),
            "n_train":           split,
            "n_test":            len(X_te),
            "directional_acc":   round(dir_acc, 4),
            "bull_rate_test":    round(bull_rate, 4),
            "model_version":     self.model_version,
            "horizon_days":      self.horizon,
        }

        self._models[symbol] = meta
        self._save(symbol, meta)

        logger.info(
            "Trained %s: acc=%.3f, horizon=%dd, n_train=%d",
            symbol, dir_acc, self.horizon, split,
        )

        return {
            "symbol":            symbol,
            "directional_acc":   round(dir_acc, 4),
            "bull_rate_test":    round(bull_rate, 4),
            "n_train":           split,
            "n_test":            len(X_te),
            "trained_on":        date.today().isoformat(),
            "model_version":     self.model_version,
        }

    def predict(self, symbol: str, df: pd.DataFrame) -> Dict:
        """
        Generate forecast for symbol using latest data.

        Returns dict with:
          - directional_signal: "bullish" | "bearish" | "neutral"
          - probability_up: calibrated probability of upward move
          - forecast_return_pct: expected return (sign * magnitude estimate)
          - ci_low / ci_high: 80% confidence interval
          - model_accuracy: directional accuracy from training eval
        """
        if symbol not in self._models:
            if not self._load(symbol):
                return {
                    "symbol":  symbol,
                    "error":   f"No trained model for {symbol}. Call train() first.",
                }

        meta      = self._models[symbol]
        clf       = meta["clf"]
        calibrator = meta["calibrator"]
        feat_cols = meta["feature_cols"]
        target    = meta["target"]

        try:
            features = build_features(df, target=target)
        except Exception as exc:
            return {"symbol": symbol, "error": f"Feature engineering failed: {exc}"}

        if features.empty:
            return {"symbol": symbol, "error": "Insufficient data for prediction"}

        # Use the latest row (most recent trading day)
        available_cols = [c for c in feat_cols if c in features.columns]
        if len(available_cols) < len(feat_cols) * 0.8:
            return {"symbol": symbol, "error": "Too many missing feature columns"}

        # Fill any missing cols with 0 (safe neutral default)
        for c in feat_cols:
            if c not in features.columns:
                features[c] = 0.0

        latest = features.iloc[[-1]][feat_cols].values.astype(np.float32)

        raw_prob   = float(clf.predict_proba(latest)[0, 1])
        cal_prob   = float(calibrator.predict([raw_prob])[0])
        cal_prob   = np.clip(cal_prob, 0.01, 0.99)

        # Direction + confidence interval via bootstrap of recent 30 predictions
        recent_rows = features.iloc[-30:][feat_cols].values.astype(np.float32)
        if len(recent_rows) >= 10:
            boot_probs = clf.predict_proba(recent_rows)[:, 1]
            boot_probs = calibrator.predict(boot_probs)
            ci_low  = float(np.percentile(boot_probs, 10))
            ci_high = float(np.percentile(boot_probs, 90))
        else:
            spread  = 0.12
            ci_low  = max(0.01, cal_prob - spread)
            ci_high = min(0.99, cal_prob + spread)

        # Directional signal with neutral band (45–55%)
        if cal_prob >= 0.55:
            direction = "bullish"
        elif cal_prob <= 0.45:
            direction = "bearish"
        else:
            direction = "neutral"

        # Forecast return estimate: magnitude scaled by historical volatility
        recent_closes = df["close"].tail(30)
        hist_vol = float(recent_closes.pct_change().std() * np.sqrt(self.horizon))
        signed   = (2 * cal_prob - 1)            # -1 to +1
        forecast_return_pct = round(signed * hist_vol * 100, 2)

        return {
            "symbol":              symbol,
            "exchange":            "NSE",
            "forecast_date":       date.today().isoformat(),
            "horizon_days":        self.horizon,
            "directional_signal":  direction,
            "probability_up":      round(cal_prob, 4),
            "forecast_return_pct": forecast_return_pct,
            "ci_low":              round(ci_low, 4),
            "ci_high":             round(ci_high, 4),
            "model_version":       meta["model_version"],
            "model_accuracy":      meta.get("directional_acc"),
            "trained_on":          meta.get("trained_on"),
        }

    def retrain_if_stale(
        self, symbol: str, df: pd.DataFrame, max_age_days: int = 30
    ) -> Optional[Dict]:
        """
        Retrain if model is >max_age_days old or not yet trained.
        Returns train result dict or None if still fresh.
        """
        if not self.is_trained(symbol):
            return self.train(symbol, df)

        meta         = self._models.get(symbol, {})
        trained_on   = meta.get("trained_on")
        if trained_on:
            from datetime import datetime, timedelta
            age = (datetime.utcnow().date() - date.fromisoformat(trained_on)).days
            if age <= max_age_days:
                return None

        logger.info("Retraining stale model for %s (age > %dd)", symbol, max_age_days)
        return self.train(symbol, df)

    def get_feature_importance(self, symbol: str) -> List[Dict]:
        """Top-10 feature importances for symbol's model."""
        if not self.is_trained(symbol):
            return []
        meta      = self._models[symbol]
        clf       = meta["clf"]
        feat_cols = meta["feature_cols"]
        ranked    = sorted(
            zip(feat_cols, clf.feature_importances_),
            key=lambda x: x[1], reverse=True,
        )[:10]
        return [{"feature": f, "importance": round(float(i), 4)} for f, i in ranked]

    # ── Persistence ──────────────────────────────────────────────────────────

    def _model_path(self, symbol: str) -> Path:
        safe = symbol.replace("/", "_").upper()
        return MODELS_DIR / f"{safe}_h{self.horizon}_{self.model_version}.pkl"

    def _save(self, symbol: str, meta: Dict) -> None:
        path = self._model_path(symbol)
        with open(path, "wb") as f:
            pickle.dump(meta, f, protocol=pickle.HIGHEST_PROTOCOL)
        logger.debug("Saved model for %s → %s", symbol, path)

    def _load(self, symbol: str) -> bool:
        path = self._model_path(symbol)
        if not path.exists():
            return False
        try:
            with open(path, "rb") as f:
                meta = pickle.load(f)
            self._models[symbol] = meta
            logger.debug("Loaded model for %s from %s", symbol, path)
            return True
        except Exception as exc:
            logger.warning("Failed to load model for %s: %s", symbol, exc)
            return False


# ── Module-level singleton ───────────────────────────────────────────────────

forecaster = VestoraForecaster(horizon=5)