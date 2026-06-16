"""
Vestora Model Evaluation
=========================
Walk-forward cross-validation enforced throughout.
No look-ahead bias. Metrics: directional accuracy, MAE, Sharpe of signal.
"""

import numpy as np
import pandas as pd
from typing import Dict, List
from datetime import date

from app.ml.feature_engineering import build_features, get_feature_cols


def walk_forward_eval(
    df: pd.DataFrame,
    symbol: str,
    initial_window: int = 252,
    step: int = 21,
    horizon: int = 5,
) -> Dict:
    """
    Walk-forward cross-validation.

    - Initial training window: 252 trading days (1 year)
    - Step: 21 days (1 month) — retrain monthly
    - No data from test period ever enters training

    Returns:
        Dict with per-fold metrics and aggregated summary.
    """
    try:
        from xgboost import XGBClassifier
    except ImportError:
        raise RuntimeError("pip install xgboost")

    target   = f"fwd_dir_{horizon}d" if horizon in [1, 5] else "fwd_dir_5d"
    features = build_features(df, target=target)

    if len(features) < initial_window + step:
        return {
            "symbol": symbol,
            "error":  f"Insufficient data: {len(features)} rows, need {initial_window + step}+",
        }

    feat_cols = get_feature_cols(features)
    X = features[feat_cols].values
    y = features[target].values
    returns = features["return_1d"].values

    folds    = []
    start    = initial_window

    while start + step <= len(X):
        X_tr, y_tr = X[:start],            y[:start]
        X_te, y_te = X[start:start+step],  y[start:start+step]
        r_te        = returns[start:start+step]

        clf = XGBClassifier(
            n_estimators=100, max_depth=4, learning_rate=0.05,
            subsample=0.8, colsample_bytree=0.8,
            min_child_weight=5, random_state=42, verbosity=0,
        )
        clf.fit(X_tr, y_tr, verbose=False)

        preds   = clf.predict(X_te)
        probs   = clf.predict_proba(X_te)[:, 1]
        correct = (preds == y_te)

        # Signal Sharpe: go long when pred=1, short when pred=0
        signal_returns = np.where(preds == 1, r_te, -r_te)
        sharpe = (
            float(signal_returns.mean() / signal_returns.std() * np.sqrt(252))
            if signal_returns.std() > 0 else 0.0
        )

        folds.append({
            "fold_start":        start,
            "fold_end":          start + step,
            "n_train":           start,
            "n_test":            step,
            "directional_acc":   float(correct.mean()),
            "signal_sharpe":     round(sharpe, 3),
            "pct_bullish_pred":  float(preds.mean()),
        })
        start += step

    if not folds:
        return {"symbol": symbol, "error": "No folds generated"}

    accs    = [f["directional_acc"] for f in folds]
    sharpes = [f["signal_sharpe"]   for f in folds]

    return {
        "symbol":           symbol,
        "horizon_days":     horizon,
        "evaluated_on":     date.today().isoformat(),
        "n_folds":          len(folds),
        "mean_accuracy":    round(float(np.mean(accs)), 4),
        "std_accuracy":     round(float(np.std(accs)),  4),
        "min_accuracy":     round(float(np.min(accs)),  4),
        "max_accuracy":     round(float(np.max(accs)),  4),
        "mean_sharpe":      round(float(np.mean(sharpes)), 3),
        "beats_random":     float(np.mean(accs)) > 0.52,
        "folds":            folds,
        "note": (
            "All metrics computed on out-of-sample data only. "
            "Past performance does not predict future results."
        ),
    }


def baseline_comparison(df: pd.DataFrame, horizon: int = 5) -> Dict:
    """
    Compare XGBoost signal against naive baselines:
    - Random (50%)
    - Always-bullish
    - Simple MA crossover (MA5 > MA20)
    """
    target   = f"fwd_dir_{horizon}d" if horizon in [1, 5] else "fwd_dir_5d"
    features = build_features(df, target=target)
    y        = features[target].values

    actual_bull_rate = float(y.mean())
    ma_cross_signal  = (features["ma5"] > features["ma20"]).astype(int).values
    ma_cross_acc     = float((ma_cross_signal == y).mean()) if len(ma_cross_signal) == len(y) else 0.5

    return {
        "actual_bullish_rate":   round(actual_bull_rate, 4),
        "random_baseline_acc":   0.50,
        "always_bullish_acc":    round(actual_bull_rate, 4),
        "ma_crossover_acc":      round(ma_cross_acc, 4),
        "note": "XGBoost must beat these to add value.",
    }


def summarise_feature_importance(symbol: str, model_meta: Dict) -> List[Dict]:
    """Return top-10 feature importances from trained XGBoost model."""
    clf       = model_meta.get("clf")
    feat_cols = model_meta.get("feature_cols", [])
    if clf is None or not feat_cols:
        return []

    importances = clf.feature_importances_
    ranked = sorted(
        zip(feat_cols, importances),
        key=lambda x: x[1], reverse=True
    )[:10]

    return [
        {"feature": feat, "importance": round(float(imp), 4)}
        for feat, imp in ranked
    ]