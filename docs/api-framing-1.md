# Vestora — API Output Framing Guide

## Purpose

This document defines the legally-safe language templates for all Vestora analytics outputs. Vestora operates as a **data and analytics platform**, not a licensed investment advisor. All outputs must be framed as data observations and model outputs — never as personalized investment recommendations.

This mirrors the operational model of Bloomberg, Reuters, and Refinitiv.

---

## The Core Distinction

| ❌ Advisory (Requires CMA License) | ✅ Analytics (Data Vendor — No License Required) |
|---|---|
| "You should buy Safaricom" | "Safaricom shows a bullish momentum signal based on 20-day RSI" |
| "We recommend selling KCB" | "KCB price is 2.3 standard deviations below its 90-day mean" |
| "This is a good investment for you" | "Historical data shows this pattern preceded a >5% move in 68% of instances" |
| "Your risk tolerance suggests X" | "The model forecast for this symbol over 5 days is X with confidence interval Y" |

---

## Standard Output Templates

### Price Forecast Output

```json
{
  "symbol": "SCOM",
  "exchange": "NSE",
  "forecast_horizon_days": 5,
  "model": "XGBoost v1.2",
  "directional_signal": "bullish",
  "forecast_return_pct": 2.4,
  "confidence_interval_low": -0.8,
  "confidence_interval_high": 5.6,
  "model_accuracy_30d": 0.61,
  "disclaimer": "This is a model forecast based on historical price and volume data. It is not investment advice. Past model accuracy does not guarantee future results.",
  "data_as_of": "2026-06-14T16:00:00Z"
}
```

### Anomaly Detection Output

```json
{
  "symbol": "EQTY",
  "exchange": "NSE",
  "anomaly_detected": true,
  "anomaly_type": "volume_spike",
  "anomaly_score": 0.87,
  "description": "Trading volume on 2026-06-14 was 4.2x the 30-day average. This statistical anomaly may indicate a significant corporate event, institutional activity, or unusual market conditions.",
  "disclaimer": "Anomaly detection identifies statistical outliers in market data. It does not constitute investment advice or imply knowledge of any specific corporate event.",
  "data_as_of": "2026-06-14T16:00:00Z"
}
```

### Market Intelligence Summary Output

```json
{
  "exchange": "NSE",
  "summary_date": "2026-06-14",
  "market_breadth": {
    "advancers": 24,
    "decliners": 18,
    "unchanged": 8
  },
  "top_momentum_signals": [
    {"symbol": "SCOM", "signal": "bullish", "strength": "strong"},
    {"symbol": "KCB", "signal": "bearish", "strength": "moderate"}
  ],
  "macro_context": "CBK held policy rate at 12.5% at last MPC meeting. KES/USD stable at 129.4.",
  "disclaimer": "Market intelligence summaries are generated from public market data and macroeconomic indicators. They represent data observations only and do not constitute investment advice.",
  "data_as_of": "2026-06-14T16:00:00Z"
}
```

---

## AI Analytics Engine — System Prompt Template

When Vestora's LLM analytics layer generates responses, the following system prompt enforces compliant framing:

```
You are Vestora's market analytics engine. You analyze East African capital market data and provide data-driven insights to users.

STRICT RULES:
1. Never tell users to buy, sell, or hold any security.
2. Never provide personalized investment advice based on a user's financial situation.
3. Always frame outputs as data observations: "The data shows...", "Historically, this pattern...", "The model indicates...", "Market data suggests..."
4. Always include the disclaimer: "This is market data analysis, not investment advice. Consult a licensed financial advisor before making investment decisions."
5. When asked for a recommendation, redirect: "I can show you what the data indicates, but investment decisions should be made with a licensed advisor who understands your full financial situation."
6. You may discuss historical patterns, model forecasts, anomaly flags, and macroeconomic context freely.
7. Cite data sources and timestamps for all factual claims.
```

---

## Disclaimer Block (All Client-Facing Outputs)

Include this disclaimer in all API responses and UI outputs:

> *Vestora provides market data, analytics, and model-generated forecasts for informational purposes only. Nothing on this platform constitutes investment advice, a solicitation, or a recommendation to buy or sell any security. All forecasts and signals are model outputs based on historical data and do not guarantee future results. Users should consult a licensed financial advisor before making investment decisions. Vestora is not licensed by the Capital Markets Authority of Kenya or any other regulatory body as an investment advisor.*

---

## Regulatory Reference

- **CMA Kenya**: Investment advice in Kenya requires authorization under the Capital Markets Act (Cap. 485A). Data vendors and analytics platforms providing general market information are not subject to this requirement provided they do not provide personalized investment advice.
- **Guiding principle**: If the output could apply to any investor equally, it's data. If it's tailored to a specific user's financial situation and tells them what to do, it's advice.

---

*Last updated: June 2026*
*Note: This document does not constitute legal advice. Vestora should seek formal legal opinion from a CMA-registered legal practitioner before commercial B2B deployment in Kenya.*
