"""
Vestora — Service Layer
Public API for all business logic. Routes import from here.
"""

from .market import get_stocks, get_stock_detail, get_forecast, get_anomalies
from .forecasting import run_forecast_for_symbol, run_batch_forecasts
from .anomaly import NSEAnomalyDetector, AnomalyResult, get_anomalies as detect_anomalies
from .analytics import run_analytics_query

__all__ = [
    # Market data
    "get_stocks",
    "get_stock_detail",
    "get_forecast",
    "get_anomalies",
    # Forecasting
    "run_forecast_for_symbol",
    "run_batch_forecasts",
    # Anomaly detection
    "NSEAnomalyDetector",
    "AnomalyResult",
    "detect_anomalies",
    # Analytics / LLM
    "run_analytics_query",
]