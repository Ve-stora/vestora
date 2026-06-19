# Vestora — Data Sources

## Overview

This document describes where Vestora's market data comes from, how it is cleaned and normalized, and at what frequency it updates. This is the first thing any B2B client or institutional partner will ask.


## Primary Data Sources

### NSE Equity Data
- **Source**: afx.kwayisi.org/nse — structured daily NSE equity prices and volumes
- **Data points**: Open, high, low, close (OHLC), volume, market cap, 52-week range
- **Update frequency**: Daily (post-market close)
- **Coverage**: All NSE-listed equities (60+ companies across Main Investment Market, Alternate Investment Market, Growth Enterprises Market)
- **Latency**: ~2–4 hours post-market close
- **Method**: Automated scraping with caching layer (24hr TTL) to respect source rate limits

### NSE Bond and Fixed Income Data
- **Source**: NSE fixed income market disclosures, CBK weekly bond auction results
- **Data points**: Yield, price, maturity, coupon, trading volume
- **Update frequency**: Weekly (auction results) + daily (secondary market)
- **Coverage**: Government bonds, corporate bonds listed on NSE

### Macroeconomic Context
- **Source**: Central Bank of Kenya (CBK) — policy rate decisions, inflation data, forex rates
- **Data points**: CBR rate, CPI, KES/USD, KES/UGX, KES/EUR
- **Update frequency**: Monthly (policy), daily (forex)

### East African Financial News (Planned — NLP Pipeline)
- **Sources**: Business Daily Africa, The EastAfrican, Capital FM Business, NSE company announcements
- **Data points**: Article headlines, body text, publication timestamp, company mentions
- **Update frequency**: Daily scrape
- **Processing**: Named entity recognition (company extraction) → sentiment scoring → feature integration



## Phase 2 Additions (USE)

### USE Equity Data
- **Source**: afx.kwayisi.org/use
- **Data points**: OHLC, volume, listed companies
- **Update frequency**: Daily
- **Coverage**: All USE-listed equities (~17 companies)

### Bank of Uganda Securities
- **Source**: Bank of Uganda T-bill and bond auction results (public disclosures)
- **Data points**: Yield, auction volume, bid-to-cover ratio
- **Update frequency**: Weekly (auction days)


## Data Pipeline Architecture

```
Raw Source → Scraper → Validation Layer → Normalization → PostgreSQL → API → Frontend
```

### Validation Layer
- Schema validation: enforce expected column types and ranges
- Missing data detection: flag counters with no trades on a given day
- Outlier flagging: z-score > 4 on daily return triggers manual review flag
- Duplicate detection: deduplicate on (symbol, date) primary key

### Normalization
- All prices stored in native currency (KES for NSE, UGX for USE)
- FX conversion available at API layer using daily CBK rates
- Volume adjusted for stock splits and rights issues where data available
- Adjusted close prices calculated where corporate action data is available

### Caching
- Raw scraped data cached for 24 hours to minimize source load
- Computed features (rolling averages, anomaly scores) cached for 1 hour
- API responses cached for 15 minutes with cache-control headers


## Data Limitations and Known Issues

| Issue | Impact | Mitigation |
|---|---|---|
| USE thin liquidity — some counters don't trade for days | Gaps in time series | Forward-fill with decay weighting; flag in API response |
| NSE historical depth limited pre-2015 | Constrains model training window | Walk-forward validation with minimum 252-day window |
| No real-time tick data | Intraday signals not possible | Day-end analytics only at current stage |
| Corporate action data incomplete | Unadjusted price series for some counters | Manual adjustment for major events; flag where uncertain |
| News NLP coverage gaps | Sentiment features missing for low-coverage companies | Fallback to price/volume features only |



## Data Access for B2B Partners

B2B clients accessing Vestora's analytics API receive:
- Normalized, cleaned data with quality flags included in API response
- Full data lineage: every analytics output includes source, timestamp, and confidence score
- Anomaly flags: outputs include `data_quality_warning` field where source data had issues
- Update webhooks: optional webhook delivery for daily data refreshes



*Last updated: June 2026*
