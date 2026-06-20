"""
Vestora ML Package
==================
Exports the module-level singletons used by the service layer.
Import these rather than instantiating new objects per-request.
"""

from app.ml.xgboost_model    import VestoraForecaster, forecaster   # noqa: F401
from app.ml.isolation_forest import VestoraAnomalyDetector, detector # noqa: F401
from app.ml.feature_engineering import build_features, get_feature_cols  # noqa: F401

__all__ = [
    "VestoraForecaster",
    "forecaster",
    "VestoraAnomalyDetector",
    "detector",
    "build_features",
    "get_feature_cols",
]