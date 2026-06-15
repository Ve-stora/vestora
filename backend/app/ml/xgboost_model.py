"""
Vestora Forecasting Engine run: pip install xgboost")

       features = self.engineer_features(df)
       if len(features) < 300:
           return {"error": f"Insufficient data for {symbol} not investment advice.
       """
       if symbol not in self.models:
           return {"error": f"No trained model for {symbol}. Run train() first."}

       model_data = self.models[symbol]
       features   = self.engineer_features(df)
       latest     = features[model_data["feature_cols"]].iloc[[-1]].values

       clf       = model_data["classifier"]
       prob_up   = float(clf.predict_proba(latest)[0][1])
       direction = "bullish" if prob_up > 0.55 else ("bearish" if prob_up < 0.45 else "neutral")

       # Rough return estimate from historical distribution of similar signals
       hist_returns = features["target_return"].values
       forecast_pct = float(np.mean(hist_returns[-20:]) * horizon * 100)
       std          = float(np.std(hist_returns[-20:]) * np.sqrt(horizon) * 100)

       return {
           "symbol":              symbol,
           "exchange":            "NSE",
           "forecast_date":       date.today().isoformat(),
           "horizon_days":        horizon,
           "directional_signal":  direction,
           "probability_up":      round(prob_up, 3),
           "forecast_return_pct": round(forecast_pct, 2),
           "ci_low":              round(forecast_pct - 1.96 * std, 2),
           "ci_high":             round(forecast_pct + 1.96 * std, 2),
           "model_version":       self.model_version,
           "model_accuracy_30d":  round(model_data["accuracy"], 3),
           "disclaimer":          "Model forecast based on historical data. Not investment advice.",
       }


forecaster = VestoraForecaster()