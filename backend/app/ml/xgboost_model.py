"""
Vestora Forecasting Engine 80% train, 20% test, strictly temporal
       split     = int(len(X) * 0.8)
       X_tr, X_te = X[:split], X[split:]
       y_tr, y_te = y[:split], y[split:]

       clf = XGBClassifier(
           n_estimators=200,
           max_depth=4,
           learning_rate=0.05,
           subsample=0.8,
           colsample_bytree=0.8,
           min_child_weight=5,    # prevents overfitting on thin data
           random_state=42,
           eval_metric="logloss",
           early_stopping_rounds=20,
           verbosity=0,
       )
       clf.fit(
           X_tr, y_tr,
           eval_set=[(X_te, y_te)],
           verbose=False,
       )

       accuracy = float((clf.predict(X_te) == y_te).mean())

       meta = {
           "clf":          clf,
           "feature_cols": feat_cols,
           "accuracy":     accuracy,
           "n_train":      split,
           "n_test":       len(X_te),
           "trained_on":   date.today().isoformat(),
       }
       self._models[symbol] = meta
       self._save(symbol, meta)

       return {
           "symbol":       symbol,
           "accuracy_30d": round(accuracy, 4),
           "n_train":      split,
           "n_test":       len(X_te),
           "model":        self.model_version,
           "horizon_days": self.horizon,
       }

   def train_all(self, data: Dict[str, pd.DataFrame]) -> Dict:
       """Batch train all symbols. Returns summary dict."""
       results = {}
       for symbol, df in data.items():
           results[symbol] = self.train(symbol, df)
       return results

   # Inference 

   def predict(self, symbol: str, df: pd.DataFrame) -> Dict:
       """
       Generate forecast for symbol.
       Returns directional signal, probability, and confidence interval.
       All output framed as model observations retrain model", "symbol": symbol}

       latest = features[available].iloc[[-1]].values
       clf    = meta["clf"]

       prob_up   = float(clf.predict_proba(latest)[0][1])
       direction = (
           "bullish" if prob_up > 0.55 else
           "bearish" if prob_up < 0.45 else
           "neutral"
       )

       # Estimate return from recent distribution
       recent_returns = features["return_1d"].tail(30).values
       forecast_pct   = float(np.mean(recent_returns) * self.horizon * 100)
       std_pct        = float(np.std(recent_returns) * np.sqrt(self.horizon) * 100)

       return {
           "symbol":              symbol,
           "exchange":            "NSE",
           "forecast_date":       date.today().isoformat(),
           "horizon_days":        self.horizon,
           "directional_signal":  direction,
           "probability_up":      round(prob_up, 3),
           "forecast_return_pct": round(forecast_pct, 2),
           "ci_low":              round(forecast_pct - 1.96 * std_pct, 2),
           "ci_high":             round(forecast_pct + 1.96 * std_pct, 2),
           "model_version":       self.model_version,
           "model_accuracy":      round(meta["accuracy"], 3),
           "trained_on":          meta.get("trained_on"),
           "disclaimer": (
               "Model forecast based on historical price and volume data. "
               "Not investment advice. Past accuracy does not guarantee future results."
           ),
       }

   # Persistence 

   def _save(self, symbol: str, meta: Dict) -> None:
       path = MODELS_DIR / f"{symbol}_xgb.pkl"
       with open(path, "wb") as f:
           pickle.dump(meta, f)

   def _load(self, symbol: str) -> Optional[Dict]:
       path = MODELS_DIR / f"{symbol}_xgb.pkl"
       if path.exists():
           with open(path, "rb") as f:
               return pickle.load(f)
       return None

   def _load_or_get(self, symbol: str) -> Optional[Dict]:
       if symbol in self._models:
           return self._models[symbol]
       meta = self._load(symbol)
       if meta:
           self._models[symbol] = meta
       return meta

   def is_trained(self, symbol: str) -> bool:
       return self._load_or_get(symbol) is not None


forecaster = VestoraForecaster(horizon=5)