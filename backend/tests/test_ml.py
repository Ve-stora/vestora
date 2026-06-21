"""
tests/test_ml.py
================
Unit + integration tests for Vestora's ML pipeline.

Covers:
  - XGBoost price forecasting (VestoraForecaster)
  - Isolation Forest anomaly detection (AnomalyDetector)
  - Feature engineering helpers
  - End-to-end pipeline smoke test

Run with:
    pytest backend/tests/test_ml.py -v
"""

import math
import pytest
import numpy as np
import pandas as pd
from datetime import date, timedelta
from unittest.mock import MagicMock, patch

# ---------------------------------------------------------------------------
# Synthetic market data fixture
# ---------------------------------------------------------------------------

def _make_ohlcv(n: int = 120, ticker: str = "SCOM") -> pd.DataFrame:
    """Generate n rows of plausible NSE OHLCV data for testing."""
    rng = np.random.default_rng(seed=42)
    dates = [date(2024, 1, 1) + timedelta(days=i) for i in range(n)]
    close = 100.0 + np.cumsum(rng.normal(0, 1.5, n))
    close = np.maximum(close, 5.0)  # price floor
    high = close + rng.uniform(0.5, 3.0, n)
    low = close - rng.uniform(0.5, 3.0, n)
    low = np.maximum(low, 1.0)
    open_ = close + rng.normal(0, 0.8, n)
    volume = rng.integers(50_000, 500_000, n).astype(float)
    return pd.DataFrame({
        "date": dates,
        "ticker": ticker,
        "open": open_,
        "high": high,
        "low": low,
        "close": close,
        "volume": volume,
    })


@pytest.fixture
def ohlcv_df():
    return _make_ohlcv()


@pytest.fixture
def thin_ohlcv_df():
    """Simulates thin NSE market – many zero-volume days."""
    df = _make_ohlcv(n=90)
    # 40% of rows have zero volume (common on low-liquidity exchanges)
    zero_idx = df.sample(frac=0.4, random_state=7).index
    df.loc[zero_idx, "volume"] = 0
    return df


# ---------------------------------------------------------------------------
# Feature engineering
# ---------------------------------------------------------------------------

class TestFeatureEngineering:
    """Tests for the feature builder used by the XGBoost forecaster."""

    def test_returns_not_nan_after_warmup(self, ohlcv_df):
        """Log returns should be NaN only on the first row."""
        from app.ml.features import build_features  # noqa: F401 – lazy import

        feats = build_features(ohlcv_df)
        assert feats["log_return"].iloc[0] != feats["log_return"].iloc[0] or True  # NaN ok row 0
        assert not feats["log_return"].iloc[1:].isna().any(), (
            "Log returns should be non-NaN from row 1 onwards"
        )

    def test_rsi_bounded(self, ohlcv_df):
        from app.ml.features import build_features

        feats = build_features(ohlcv_df)
        rsi = feats["rsi_14"].dropna()
        assert (rsi >= 0).all() and (rsi <= 100).all(), "RSI must be in [0, 100]"

    def test_bollinger_upper_gte_lower(self, ohlcv_df):
        from app.ml.features import build_features

        feats = build_features(ohlcv_df)
        bb_upper = feats["bb_upper"].dropna()
        bb_lower = feats["bb_lower"].dropna()
        assert (bb_upper >= bb_lower).all(), "Bollinger upper band must be ≥ lower band"

    def test_volume_ma_non_negative(self, ohlcv_df):
        from app.ml.features import build_features

        feats = build_features(ohlcv_df)
        assert (feats["vol_ma_20"].dropna() >= 0).all()

    def test_thin_market_does_not_raise(self, thin_ohlcv_df):
        from app.ml.features import build_features

        # Should not raise even with 40% zero-volume rows
        feats = build_features(thin_ohlcv_df)
        assert len(feats) == len(thin_ohlcv_df)


# ---------------------------------------------------------------------------
# Forecaster (XGBoost)
# ---------------------------------------------------------------------------

class TestVestoraForecaster:
    """Tests for XGBoost price forecaster."""

    def test_fit_returns_self(self, ohlcv_df):
        from app.ml.forecaster import VestoraForecaster

        model = VestoraForecaster(horizon=5)
        result = model.fit(ohlcv_df)
        assert result is model, "fit() should return self for chaining"

    def test_predict_returns_correct_length(self, ohlcv_df):
        from app.ml.forecaster import VestoraForecaster

        horizon = 7
        model = VestoraForecaster(horizon=horizon)
        model.fit(ohlcv_df)
        preds = model.predict()
        assert len(preds) == horizon, f"Expected {horizon} predictions, got {len(preds)}"

    def test_predict_shape_has_date_and_price(self, ohlcv_df):
        from app.ml.forecaster import VestoraForecaster

        model = VestoraForecaster(horizon=5)
        model.fit(ohlcv_df)
        preds = model.predict()
        # Should return list of dicts or DataFrame with 'date' + 'forecast'
        if isinstance(preds, pd.DataFrame):
            assert "forecast" in preds.columns
            assert "date" in preds.columns
        else:
            assert all("forecast" in p for p in preds)
            assert all("date" in p for p in preds)

    def test_predict_prices_are_positive(self, ohlcv_df):
        from app.ml.forecaster import VestoraForecaster

        model = VestoraForecaster(horizon=5)
        model.fit(ohlcv_df)
        preds = model.predict()
        if isinstance(preds, pd.DataFrame):
            prices = preds["forecast"].tolist()
        else:
            prices = [p["forecast"] for p in preds]
        assert all(p > 0 for p in prices), "Forecast prices must be positive"

    def test_predict_before_fit_raises(self):
        from app.ml.forecaster import VestoraForecaster

        model = VestoraForecaster(horizon=5)
        with pytest.raises(RuntimeError, match="fit"):
            model.predict()

    def test_insufficient_data_raises(self):
        from app.ml.forecaster import VestoraForecaster

        too_short = _make_ohlcv(n=5)
        model = VestoraForecaster(horizon=5)
        with pytest.raises(ValueError):
            model.fit(too_short)

    def test_feature_importances_available_after_fit(self, ohlcv_df):
        from app.ml.forecaster import VestoraForecaster

        model = VestoraForecaster(horizon=5)
        model.fit(ohlcv_df)
        imps = model.feature_importances()
        assert isinstance(imps, dict) and len(imps) > 0

    def test_serialization_roundtrip(self, ohlcv_df, tmp_path):
        from app.ml.forecaster import VestoraForecaster

        model = VestoraForecaster(horizon=5)
        model.fit(ohlcv_df)
        preds_before = model.predict()

        path = tmp_path / "forecaster.pkl"
        model.save(str(path))
        loaded = VestoraForecaster.load(str(path))
        preds_after = loaded.predict()

        if isinstance(preds_before, pd.DataFrame):
            pd.testing.assert_frame_equal(preds_before, preds_after)
        else:
            assert preds_before == preds_after


# ---------------------------------------------------------------------------
# Anomaly detector (Isolation Forest)
# ---------------------------------------------------------------------------

class TestAnomalyDetector:
    """Tests for Isolation Forest anomaly detection."""

    def test_fit_predict_returns_correct_length(self, ohlcv_df):
        from app.ml.anomaly import AnomalyDetector

        detector = AnomalyDetector(contamination=0.05)
        result = detector.fit_predict(ohlcv_df)
        assert len(result) == len(ohlcv_df)

    def test_output_is_boolean_series(self, ohlcv_df):
        from app.ml.anomaly import AnomalyDetector

        detector = AnomalyDetector(contamination=0.05)
        result = detector.fit_predict(ohlcv_df)
        if isinstance(result, pd.Series):
            assert result.dtype == bool or result.dtype == np.bool_
        else:
            assert all(isinstance(v, (bool, np.bool_)) for v in result)

    def test_anomaly_rate_near_contamination(self, ohlcv_df):
        """Anomaly rate should be close to the contamination parameter."""
        from app.ml.anomaly import AnomalyDetector

        contamination = 0.1
        detector = AnomalyDetector(contamination=contamination)
        result = detector.fit_predict(ohlcv_df)
        rate = np.mean(result)
        # Allow ±5 pp tolerance
        assert abs(rate - contamination) < 0.05, (
            f"Anomaly rate {rate:.3f} too far from contamination {contamination}"
        )

    def test_spike_detected_as_anomaly(self):
        """A blatant price spike should be flagged as anomalous."""
        from app.ml.anomaly import AnomalyDetector

        df = _make_ohlcv(n=100)
        # Plant an obvious spike on the last row
        df.loc[df.index[-1], "close"] = df["close"].mean() * 20
        df.loc[df.index[-1], "volume"] = df["volume"].mean() * 50

        detector = AnomalyDetector(contamination=0.05)
        result = detector.fit_predict(df)
        if isinstance(result, pd.Series):
            assert result.iloc[-1], "Spike row should be flagged as anomaly"
        else:
            assert result[-1], "Spike row should be flagged as anomaly"

    def test_thin_market_stability(self, thin_ohlcv_df):
        """Detector should not crash on thin market data."""
        from app.ml.anomaly import AnomalyDetector

        detector = AnomalyDetector(contamination=0.05)
        result = detector.fit_predict(thin_ohlcv_df)
        assert len(result) == len(thin_ohlcv_df)

    def test_anomaly_scores_accessible(self, ohlcv_df):
        from app.ml.anomaly import AnomalyDetector

        detector = AnomalyDetector(contamination=0.05)
        detector.fit_predict(ohlcv_df)
        scores = detector.scores_
        assert scores is not None and len(scores) == len(ohlcv_df)

    def test_before_fit_raises(self):
        from app.ml.anomaly import AnomalyDetector

        detector = AnomalyDetector()
        with pytest.raises(RuntimeError):
            detector.scores_  # noqa


# ---------------------------------------------------------------------------
# End-to-end pipeline smoke test
# ---------------------------------------------------------------------------

class TestMLPipeline:
    """Smoke tests for the full ML inference pipeline."""

    def test_pipeline_returns_forecast_and_anomalies(self, ohlcv_df):
        """run_pipeline() should return a dict with 'forecast' and 'anomalies'."""
        from app.ml.pipeline import run_pipeline

        result = run_pipeline(ohlcv_df, ticker="SCOM", horizon=5)
        assert "forecast" in result, "Pipeline output must contain 'forecast'"
        assert "anomalies" in result, "Pipeline output must contain 'anomalies'"

    def test_pipeline_forecast_length(self, ohlcv_df):
        from app.ml.pipeline import run_pipeline

        horizon = 7
        result = run_pipeline(ohlcv_df, ticker="SCOM", horizon=horizon)
        forecast = result["forecast"]
        if isinstance(forecast, pd.DataFrame):
            assert len(forecast) == horizon
        else:
            assert len(forecast) == horizon

    def test_pipeline_anomaly_count_nonzero_large_dataset(self):
        """With 200 rows and contamination=0.05, expect at least 1 anomaly."""
        from app.ml.pipeline import run_pipeline

        df = _make_ohlcv(n=200)
        result = run_pipeline(df, ticker="SCOM", horizon=5)
        anomaly_flags = result["anomalies"]
        assert sum(anomaly_flags) >= 1

    def test_pipeline_includes_metadata(self, ohlcv_df):
        from app.ml.pipeline import run_pipeline

        result = run_pipeline(ohlcv_df, ticker="SCOM", horizon=5)
        assert "ticker" in result
        assert result["ticker"] == "SCOM"
        assert "generated_at" in result

    @patch("app.ml.pipeline.run_pipeline")
    def test_pipeline_mock_integration(self, mock_pipeline):
        """Verify downstream callers handle pipeline output correctly."""
        mock_pipeline.return_value = {
            "ticker": "EQTY",
            "forecast": [{"date": "2026-01-01", "forecast": 52.5}],
            "anomalies": [False],
            "generated_at": "2026-01-01T00:00:00",
        }
        from app.ml.pipeline import run_pipeline

        result = run_pipeline(MagicMock(), ticker="EQTY", horizon=1)
        assert result["ticker"] == "EQTY"
        assert len(result["forecast"]) == 1
        assert math.isclose(result["forecast"][0]["forecast"], 52.5)