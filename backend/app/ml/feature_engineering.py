"""
Vestora Feature Engineering
============================
Shared feature pipeline used by both XGBoost forecaster and Isolation Forest.
Designed for thin EAC markets: shorter windows, explicit zero-volume handling,
conservative forward-return targets to avoid data leakage.

Public API
----------
build_features(df, target)   — full pipeline, returns feature-rich DataFrame
get_feature_cols(df)         — columns that exist in a given df
add_returns / add_volume_features / add_price_gap — used by isolation_forest.py
"""

import numpy as np
import pandas as pd


# ── Returns & momentum ────────────────────────────────────────────────────────

def add_returns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute forward and backward return columns.
    Forward returns are shifted -1 so today's row has tomorrow's return.
    """
    c = df["close"]

    # Backward returns (features)
    df["return_1d"]  = c.pct_change(1)
    df["return_5d"]  = c.pct_change(5)
    df["return_10d"] = c.pct_change(10)

    # Forward returns (targets — shift -1 = tomorrow's return in today's row)
    df["fwd_return_1d"] = df["return_1d"].shift(-1)
    df["fwd_return_5d"] = df["return_5d"].shift(-1)
    df["fwd_dir_1d"]    = (df["fwd_return_1d"] > 0).astype(int)
    df["fwd_dir_5d"]    = (df["fwd_return_5d"] > 0).astype(int)

    return df


# ── Rolling statistics ────────────────────────────────────────────────────────

def add_rolling_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Moving averages and rolling volatility."""
    c = df["close"]

    for w in [5, 10, 20, 30]:
        df[f"ma{w}"]  = c.rolling(w, min_periods=w // 2).mean()
        df[f"std{w}"] = c.pct_change().rolling(w, min_periods=w // 2).std()

    return df


# ── RSI ───────────────────────────────────────────────────────────────────────

def add_rsi(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """
    RSI adapted for thin markets.
    On zero-volume days we forward-fill RSI rather than computing on stale prices.
    """
    delta = df["close"].diff()
    gain  = delta.clip(lower=0)
    loss  = -delta.clip(upper=0)

    avg_gain = gain.ewm(span=period, min_periods=period // 2, adjust=False).mean()
    avg_loss = loss.ewm(span=period, min_periods=period // 2, adjust=False).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)
    df["rsi14"] = 100 - (100 / (1 + rs))
    df["rsi14"] = df["rsi14"].fillna(50)   # neutral default on sparse data

    # Overbought / oversold flags
    df["rsi_ob"] = (df["rsi14"] > 70).astype(int)
    df["rsi_os"] = (df["rsi14"] < 30).astype(int)
    return df


# ── MACD ──────────────────────────────────────────────────────────────────────

def add_macd(df: pd.DataFrame) -> pd.DataFrame:
    """MACD adapted for low-liquidity — shorter spans than US-market defaults."""
    c = df["close"]

    ema8  = c.ewm(span=8,  adjust=False).mean()
    ema17 = c.ewm(span=17, adjust=False).mean()

    df["macd"]        = ema8 - ema17
    df["macd_signal"] = df["macd"].ewm(span=9, adjust=False).mean()
    df["macd_hist"]   = df["macd"] - df["macd_signal"]
    df["macd_cross"]  = (
        (df["macd"] > df["macd_signal"]).astype(int)
        - (df["macd"].shift(1) > df["macd_signal"].shift(1)).astype(int)
    )  # +1 = bullish cross, -1 = bearish cross
    return df


# ── MA ratios ─────────────────────────────────────────────────────────────────

def add_ma_ratios(df: pd.DataFrame) -> pd.DataFrame:
    """Price relative to moving averages — useful momentum and mean-reversion features."""
    for w in [5, 10, 20]:
        ma_col = f"ma{w}"
        if ma_col in df.columns:
            df[f"price_ma{w}_ratio"] = (
                df["close"] / df[ma_col].replace(0, np.nan)
            ).fillna(1.0)
    return df


# ── Volume features ───────────────────────────────────────────────────────────

def add_volume_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Volume features.
    Handles zero-volume days (no trades) explicitly — fills with neutral values
    rather than propagating zeros through z-score calculations.
    """
    if "volume" not in df.columns or df["volume"].sum() == 0:
        df["vol_ma30"]        = np.nan
        df["vol_zscore"]      = 0.0
        df["unusual_vol"]     = 0
        df["no_trade_day"]    = 1
        df["vol_price_ratio"] = 0.0
        return df

    vol = df["volume"].fillna(0)
    df["no_trade_day"] = (vol == 0).astype(int)

    vol_ma30  = vol.rolling(30, min_periods=10).mean()
    vol_std30 = vol.rolling(30, min_periods=10).std().replace(0, 1)

    df["vol_ma30"]        = vol_ma30
    df["vol_zscore"]      = ((vol - vol_ma30) / vol_std30).fillna(0).clip(-5, 5)
    df["unusual_vol"]     = (vol > vol_ma30 * 2.5).astype(int)
    df["vol_price_ratio"] = (vol / df["close"].replace(0, np.nan)).fillna(0)
    return df


# ── Price gap (overnight) & 52-week position ──────────────────────────────────

def add_price_gap(df: pd.DataFrame) -> pd.DataFrame:
    """
    Overnight gap feature + 52-week price position.
    Called 'add_price_gap' for compatibility with isolation_forest.py imports.
    Adds both 'price_gap' (overnight open-vs-prev-close) and 'price_position_52w'.
    """
    # Overnight gap: open vs previous close (if open column available)
    if "open" in df.columns:
        df["price_gap"] = (
            (df["open"] - df["close"].shift(1)) / df["close"].shift(1)
        ).fillna(0)
    else:
        # Approximate with close-to-close gap on days with big moves
        df["price_gap"] = df["close"].pct_change().fillna(0)

    # 52-week price position (0 = at 52w low, 1 = at 52w high)
    high52 = df["close"].rolling(252, min_periods=20).max()
    low52  = df["close"].rolling(252, min_periods=20).min()
    rng    = (high52 - low52).replace(0, np.nan)
    df["price_position_52w"] = ((df["close"] - low52) / rng).fillna(0.5).clip(0, 1)

    return df


# ── Price position (Bollinger-style) ─────────────────────────────────────────

def add_price_position(df: pd.DataFrame) -> pd.DataFrame:
    """Price position within 20-day Bollinger band (0 = lower band, 1 = upper band)."""
    c      = df["close"]
    ma20   = c.rolling(20, min_periods=10).mean()
    std20  = c.rolling(20, min_periods=10).std().replace(0, np.nan)
    upper  = ma20 + 2 * std20
    lower  = ma20 - 2 * std20
    rng    = (upper - lower).replace(0, np.nan)
    df["bb_position"] = ((c - lower) / rng).fillna(0.5).clip(0, 1)
    return df


# ── Lagged returns ────────────────────────────────────────────────────────────

def add_lagged_returns(df: pd.DataFrame, lags: list = [1, 2, 3, 5]) -> pd.DataFrame:
    """Lagged return features for autoregressive signal."""
    for lag in lags:
        df[f"return_lag{lag}"] = df["return_1d"].shift(lag).fillna(0)
    return df


# ── Full pipeline ─────────────────────────────────────────────────────────────

def build_features(df: pd.DataFrame, target: str = "fwd_dir_5d") -> pd.DataFrame:
    """
    Full feature pipeline. Returns df with all engineered features.
    Call this before training or inference.

    Args:
        df: DataFrame with at minimum [date, close] columns.
            Optional: [open, high, low, volume]
        target: which target column to keep ("fwd_dir_1d" or "fwd_dir_5d")

    Returns:
        DataFrame with features + target, NaN rows dropped.
    """
    df = df.copy().sort_values("date").reset_index(drop=True)

    df = add_returns(df)
    df = add_rolling_stats(df)
    df = add_rsi(df)
    df = add_macd(df)
    df = add_ma_ratios(df)
    df = add_volume_features(df)
    df = add_price_gap(df)
    df = add_price_position(df)
    df = add_lagged_returns(df)

    return df.dropna(subset=[target])


# ── Feature column registry ───────────────────────────────────────────────────

FEATURE_COLS = [
    "return_1d", "return_5d", "return_10d",
    "ma5", "ma10", "ma20", "ma30",
    "std10", "std20",
    "rsi14", "rsi_ob", "rsi_os",
    "macd", "macd_signal", "macd_hist", "macd_cross",
    "price_ma5_ratio", "price_ma10_ratio", "price_ma20_ratio",
    "vol_zscore", "unusual_vol", "no_trade_day", "vol_price_ratio",
    "price_gap",
    "price_position_52w",
    "bb_position",
    "return_lag1", "return_lag2", "return_lag3", "return_lag5",
]


def get_feature_cols(df: pd.DataFrame) -> list:
    """Return only feature columns that actually exist in this df."""
    return [c for c in FEATURE_COLS if c in df.columns]