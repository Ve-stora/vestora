"""
Vestora Feature Engineering
============================
Shared feature pipeline used by both XGBoost forecaster and Isolation Forest.
Designed for thin EAC markets shift -1 so today's row has tomorrow's return)
   df["fwd_return_1d"] = df["return_1d"].shift(-1)
   df["fwd_return_5d"] = df["return_5d"].shift(-1)
   df["fwd_dir_1d"]    = (df["fwd_return_1d"] > 0).astype(int)
   df["fwd_dir_5d"]    = (df["fwd_return_5d"] > 0).astype(int)
   return df


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
   df["rsi14"] = df["rsi14"].fillna(50)  # neutral default on sparse data

   # Overbought/oversold flags
   df["rsi_ob"] = (df["rsi14"] > 70).astype(int)
   df["rsi_os"] = (df["rsi14"] < 30).astype(int)
   return df


def add_macd(df: pd.DataFrame) -> pd.DataFrame:
   """MACD adapted for low-liquidity strong features for momentum."""
   for w in [5, 10, 20]:
       ma_col = f"ma{w}"
       if ma_col in df.columns:
           df[f"price_ma{w}_ratio"] = (
               df["close"] / df[ma_col].replace(0, np.nan)
           ).fillna(1.0)
   return df


def add_volume_features(df: pd.DataFrame) -> pd.DataFrame:
   """
   Volume features.
   Handles zero-volume days (no trades) explicitly fill with neutral values
       df["vol_ma30"]       = np.nan
       df["vol_zscore"]     = 0.0
       df["unusual_vol"]    = 0
       df["no_trade_day"]   = 1
       return df

   vol = df["volume"].fillna(0)
   df["no_trade_day"] = (vol == 0).astype(int)

   vol_ma30  = vol.rolling(30, min_periods=10).mean()
   vol_std30 = vol.rolling(30, min_periods=10).std().replace(0, 1)

   df["vol_ma30"]    = vol_ma30
   df["vol_zscore"]  = ((vol - vol_ma30) / vol_std30).fillna(0).clip(-5, 5)
   df["unusual_vol"] = (vol > vol_ma30 * 2.5).astype(int)
   df["vol_price_ratio"] = (vol / df["close"].replace(0, np.nan)).fillna(0)
   return df


def add_price_gap(df: pd.DataFrame) -> pd.DataFrame:
   """Overnight gap useful momentum context."""
   high52 = df["close"].rolling(252, min_periods=20).max()
   low52  = df["close"].rolling(252, min_periods=20).min()
   rng    = (high52 - low52).replace(0, np.nan)
   df["price_position_52w"] = ((df["close"] - low52) / rng).fillna(0.5).clip(0, 1)
   return df


def add_lagged_returns(df: pd.DataFrame, lags: list = [1, 2, 3, 5]) -> pd.DataFrame:
   """Lagged return features for autoregressive signal."""
   for lag in lags:
       df[f"return_lag{lag}"] = df["return_1d"].shift(lag).fillna(0)
   return df


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
   "return_lag1", "return_lag2", "return_lag3", "return_lag5",
]


def get_feature_cols(df: pd.DataFrame) -> list:
   """Return only feature columns that actually exist in this df."""
   return [c for c in FEATURE_COLS if c in df.columns]