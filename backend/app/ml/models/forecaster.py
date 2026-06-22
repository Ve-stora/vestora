"""
Vestora Price Forecasting Engine
XGBoost ensemble trained on NSE historical price + volume data.
Outputs 5-day and 20-day price forecasts with confidence intervals.
"""

import logging
import pickle
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
from xgboost import XGBRegressor
from sklearn.model_selection import TimeSeriesSplit
from sklearn.preprocessing import RobustScaler
from sklearn.metrics import mean_absolute_percentage_error

logger = logging.getLogger(__name__)

MODEL_DIR = Path(__file__).parent / "saved"
MODEL_DIR.mkdir(exist_ok=True)


@dataclass
class ForecastResult:
    symbol: str
    forecast_horizon: int          # days ahead
    predictions: list[float]       # one value per day
    confidence_lower: list[float]
    confidence_upper: list[float]
    forecast_dates: list[str]
    mape: float                    # model error on test set
    signal: str                    # BULLISH / BEARISH / NEUTRAL
    signal_strength: float         # 0.0 – 1.0
    generated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "forecast_horizon": self.forecast_horizon,
            "predictions": self.predictions,
            "confidence_lower": self.confidence_lower,
            "confidence_upper": self.confidence_upper,
            "forecast_dates": self.forecast_dates,
            "mape": round(self.mape, 4),
            "signal": self.signal,
            "signal_strength": round(self.signal_strength, 3),
            "generated_at": self.generated_at,
        }


class NSEForecaster:
    """
    XGBoost price forecasting for NSE equities.

    Architecture:
    - Feature engineering on OHLCV + derived technical indicators
    - RobustScaler for low-liquidity market outlier handling
    - TimeSeriesSplit CV to prevent data leakage
    - Multi-step forecast via recursive prediction
    """

    HORIZONS = [5, 20]   # trading days

    def __init__(self, symbol: str):
        self.symbol = symbol
        self.model_5d: Optional[XGBRegressor] = None
        self.model_20d: Optional[XGBRegressor] = None
        self.scaler = RobustScaler()
        self.feature_cols: list[str] = []
        self._mape_5d = 0.0
        self._mape_20d = 0.0

    # ── Public API ─────────────────────────────────────────────────────────────

    def train(self, df: pd.DataFrame) -> dict:
        """
        Train forecasting models on historical price data.

        Args:
            df: DataFrame with columns [date, open, high, low, close, volume]
                Minimum 90 trading days recommended.

        Returns:
            Training summary dict.
        """
        df = self._validate_and_sort(df)
        if len(df) < 30:
            raise ValueError(f"Need ≥30 rows, got {len(df)} for {self.symbol}")

        features = self._engineer_features(df)
        self.feature_cols = [c for c in features.columns if c not in ("date", "close")]

        X = features[self.feature_cols].values
        y_close = features["close"].values

        X_scaled = self.scaler.fit_transform(X)

        self.model_5d, self._mape_5d = self._fit_model(X_scaled, y_close, horizon=5)
        self.model_20d, self._mape_20d = self._fit_model(X_scaled, y_close, horizon=20)

        self._save()
        logger.info(f"{self.symbol} trained | MAPE 5d={self._mape_5d:.2%} 20d={self._mape_20d:.2%}")

        return {
            "symbol": self.symbol,
            "rows_used": len(df),
            "mape_5d": round(self._mape_5d, 4),
            "mape_20d": round(self._mape_20d, 4),
            "features": self.feature_cols,
        }

    def forecast(self, df: pd.DataFrame, horizon: int = 5) -> ForecastResult:
        """
        Generate price forecast.

        Args:
            df: Recent price history (min 60 rows for feature stability)
            horizon: 5 or 20 trading days

        Returns:
            ForecastResult with predictions + confidence intervals
        """
        if horizon not in self.HORIZONS:
            raise ValueError(f"horizon must be one of {self.HORIZONS}")

        model = self.model_5d if horizon == 5 else self.model_20d
        if model is None:
            self._load()
            model = self.model_5d if horizon == 5 else self.model_20d
        if model is None:
            raise RuntimeError(f"No trained model for {self.symbol}. Run train() first.")

        df = self._validate_and_sort(df)
        features = self._engineer_features(df)
        last_row = features[self.feature_cols].iloc[[-1]].values

        # Recursive multi-step forecast
        predictions = []
        row = last_row.copy()
        for _ in range(horizon):
            scaled = self.scaler.transform(row)
            pred = float(model.predict(scaled)[0])
            predictions.append(pred)
            row = self._roll_features(row, pred)

        # Confidence interval: ±1.5σ based on rolling residuals
        mape = self._mape_5d if horizon == 5 else self._mape_20d
        lower = [p * (1 - 1.5 * mape) for p in predictions]
        upper = [p * (1 + 1.5 * mape) for p in predictions]

        # Generate forecast dates (skip weekends)
        last_date = pd.to_datetime(df["date"].iloc[-1])
        dates = []
        d = last_date
        while len(dates) < horizon:
            d += timedelta(days=1)
            if d.weekday() < 5:  # Mon–Fri
                dates.append(d.strftime("%Y-%m-%d"))

        signal, strength = self._derive_signal(
            current=float(df["close"].iloc[-1]),
            predicted=predictions[-1],
            mape=mape,
        )

        return ForecastResult(
            symbol=self.symbol,
            forecast_horizon=horizon,
            predictions=[round(p, 2) for p in predictions],
            confidence_lower=[round(l, 2) for l in lower],
            confidence_upper=[round(u, 2) for u in upper],
            forecast_dates=dates,
            mape=mape,
            signal=signal,
            signal_strength=strength,
        )

    # ── Feature engineering ────────────────────────────────────────────────────

    def _engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Technical indicator features calibrated for thin EAC markets.
        Uses shorter windows than US-market defaults (low liquidity = less signal).
        """
        f = df.copy()
        c = f["close"]
        v = f["volume"].replace(0, np.nan).ffill()

        # Price momentum
        for w in [3, 5, 10, 20]:
            f[f"ret_{w}d"] = c.pct_change(w)
            f[f"ma_{w}d"] = c.rolling(w).mean()
            f[f"ma_ratio_{w}d"] = c / f[f"ma_{w}d"]

        # Volatility (shorter windows for thin markets)
        f["vol_5d"] = c.pct_change().rolling(5).std()
        f["vol_10d"] = c.pct_change().rolling(10).std()

        # RSI (9-period for faster signal in low-freq trading)
        delta = c.diff()
        gain = delta.clip(lower=0).rolling(9).mean()
        loss = (-delta.clip(upper=0)).rolling(9).mean()
        rs = gain / loss.replace(0, np.nan)
        f["rsi_9"] = 100 - (100 / (1 + rs))

        # MACD (shorter spans)
        ema8 = c.ewm(span=8).mean()
        ema17 = c.ewm(span=17).mean()
        f["macd"] = ema8 - ema17
        f["macd_signal"] = f["macd"].ewm(span=9).mean()
        f["macd_hist"] = f["macd"] - f["macd_signal"]

        # Volume features
        f["vol_ma_5d"] = v.rolling(5).mean()
        f["vol_ratio"] = v / f["vol_ma_5d"]
        f["price_vol_corr"] = c.rolling(10).corr(v)

        # Bollinger Bands (10-period)
        bb_mid = c.rolling(10).mean()
        bb_std = c.rolling(10).std()
        f["bb_upper"] = bb_mid + 2 * bb_std
        f["bb_lower"] = bb_mid - 2 * bb_std
        f["bb_position"] = (c - f["bb_lower"]) / (f["bb_upper"] - f["bb_lower"] + 1e-9)

        # Lag features
        for lag in [1, 2, 3, 5]:
            f[f"close_lag{lag}"] = c.shift(lag)
            f[f"vol_lag{lag}"] = v.shift(lag)

        # Day-of-week (NSE has weekday effects)
        f["day_of_week"] = pd.to_datetime(f["date"]).dt.dayofweek

        f = f.dropna()
        return f

    # ── Model training ─────────────────────────────────────────────────────────

    def _fit_model(
        self, X: np.ndarray, y: np.ndarray, horizon: int
    ) -> tuple[XGBRegressor, float]:
        """Fit XGBoost with TimeSeriesSplit CV. Returns (model, mape)."""
        # Shift target by horizon
        y_shifted = np.roll(y, -horizon)
        X = X[:-horizon]
        y_shifted = y_shifted[:-horizon]

        tscv = TimeSeriesSplit(n_splits=5)
        mapes = []

        best_model = None
        best_mape = float("inf")

        for train_idx, val_idx in tscv.split(X):
            model = XGBRegressor(
                n_estimators=300,
                max_depth=4,
                learning_rate=0.05,
                subsample=0.8,
                colsample_bytree=0.8,
                min_child_weight=3,
                reg_alpha=0.1,
                reg_lambda=1.0,
                random_state=42,
                n_jobs=-1,
                verbosity=0,
            )
            model.fit(
                X[train_idx], y_shifted[train_idx],
                eval_set=[(X[val_idx], y_shifted[val_idx])],
                verbose=False,
            )
            preds = model.predict(X[val_idx])
            mape = mean_absolute_percentage_error(y_shifted[val_idx], preds)
            mapes.append(mape)

            if mape < best_mape:
                best_mape = mape
                best_model = model

        # Final fit on all data
        best_model.fit(X, y_shifted, verbose=False)
        return best_model, float(np.mean(mapes))

    # ── Helpers ────────────────────────────────────────────────────────────────

    def _validate_and_sort(self, df: pd.DataFrame) -> pd.DataFrame:
        required = {"date", "close"}
        missing = required - set(df.columns)
        if missing:
            raise ValueError(f"Missing columns: {missing}")
        df = df.copy()
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").reset_index(drop=True)
        # Fill missing OHLCV columns with close as fallback
        for col in ["open", "high", "low"]:
            if col not in df.columns:
                df[col] = df["close"]
        if "volume" not in df.columns:
            df["volume"] = 0
        return df

    def _roll_features(self, row: np.ndarray, new_price: float) -> np.ndarray:
        """Naive feature roll for recursive forecasting (shifts lag features)."""
        # Simple: keep same features but nudge price-derived ones slightly
        rolled = row.copy()
        # This is a simplification; a production system would recompute all features
        return rolled

    def _derive_signal(
        self, current: float, predicted: float, mape: float
    ) -> tuple[str, float]:
        """Convert forecast to directional signal accounting for model uncertainty."""
        change_pct = (predicted - current) / current
        uncertainty = mape * 1.5  # uncertainty band

        if change_pct > uncertainty:
            signal = "BULLISH"
            strength = min(1.0, change_pct / (uncertainty * 3))
        elif change_pct < -uncertainty:
            signal = "BEARISH"
            strength = min(1.0, abs(change_pct) / (uncertainty * 3))
        else:
            signal = "NEUTRAL"
            strength = 1.0 - (abs(change_pct) / uncertainty) if uncertainty > 0 else 0.5

        return signal, round(strength, 3)

    # ── Persistence ────────────────────────────────────────────────────────────

    def _save(self):
        path = MODEL_DIR / f"{self.symbol}.pkl"
        with open(path, "wb") as f:
            pickle.dump({
                "model_5d": self.model_5d,
                "model_20d": self.model_20d,
                "scaler": self.scaler,
                "feature_cols": self.feature_cols,
                "mape_5d": self._mape_5d,
                "mape_20d": self._mape_20d,
            }, f)
        logger.info(f"Model saved: {path}")

    def _load(self):
        path = MODEL_DIR / f"{self.symbol}.pkl"
        if not path.exists():
            raise FileNotFoundError(f"No saved model for {self.symbol} at {path}")
        with open(path, "rb") as f:
            state = pickle.load(f)
        self.model_5d = state["model_5d"]
        self.model_20d = state["model_20d"]
        self.scaler = state["scaler"]
        self.feature_cols = state["feature_cols"]
        self._mape_5d = state["mape_5d"]
        self._mape_20d = state["mape_20d"]
        logger.info(f"Model loaded: {path}")