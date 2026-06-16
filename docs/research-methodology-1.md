# Vestora — Research Methodology

## Overview

Vestora's ML components address underexplored problems in computational finance — specifically the application of modern forecasting and anomaly detection techniques to thin, low-liquidity emerging market exchanges in East Africa. This document outlines the data sources, model architecture, evaluation approach, and open research questions.

---

## 1. Problem Statement

East African capital markets (NSE, USE, DSE, RSE) present unique challenges that make standard financial ML approaches insufficient:

- **Low liquidity**: Many counters trade infrequently, creating sparse time-series data
- **Thin order books**: Price movements are often driven by a small number of large trades rather than continuous market activity
- **Data scarcity**: Limited historical depth compared to US/EU markets; inconsistent data availability
- **Structural market differences**: Thin retail participation, high institutional concentration, cross-listing effects across EAC exchanges

These conditions make standard LSTM/Transformer forecasting models — trained on deep, liquid markets — unreliable without significant adaptation.

---

## 2. Data Sources

| Source | Data Type | Update Frequency | Notes |
|---|---|---|---|
| afx.kwayisi.org/nse | NSE equity prices, volumes | Daily | Primary scraping target |
| afx.kwayisi.org/use | USE equity prices | Daily | Phase 2 |
| Central Bank of Kenya | T-bill and bond yields | Weekly | Macroeconomic context |
| Bank of Uganda | BOU rate decisions, T-bill yields | Monthly | Phase 2 |
| Local financial news (Business Daily, The EastAfrican) | Textual sentiment | Daily | NLP pipeline |

### Data Cleaning Pipeline
1. Detect and handle missing trading days (exchange holidays, illiquid counters)
2. Outlier detection — flag single-trade price spikes vs. genuine movements
3. Volume normalization — adjust for thin-market trading patterns
4. Forward-fill strategy for infrequently traded counters with decay weighting

---

## 3. Model Architecture

### 3.1 Price Forecasting — XGBoost Ensemble

**Why XGBoost over deep learning**: Deep learning models (LSTM, Transformer) require large training datasets to generalise. NSE historical data depth is insufficient for reliable deep learning without transfer learning from liquid markets — which introduces distributional shift problems. XGBoost with engineered features performs comparably or better on thin-market tabular time-series.

**Feature Engineering**:
- Rolling statistics: 5, 10, 20, 30-day moving averages and standard deviations
- Momentum indicators: RSI, MACD adapted for thin-market conditions
- Volume features: volume/price ratio, unusual volume flags
- Macro features: KES/USD rate, CBK policy rate, regional commodity prices (relevant for sector analysis)
- Cross-listing features: NSE/USE spread for dual-listed securities

**Target**: Next-day and next-5-day directional price movement (classification) and magnitude (regression)

**Evaluation**: Walk-forward cross-validation to prevent data leakage. Metrics: directional accuracy, MAE, Sharpe ratio of signal.

### 3.2 Anomaly Detection — Isolation Forest

**Application**: Detect unusual trading activity — volume spikes, price discontinuities, bid-ask anomalies — that may indicate insider trading, market manipulation, or significant corporate events before public announcement.

**Features**: Price return z-score, volume deviation from rolling baseline, bid-ask spread anomaly, time-of-day patterns

**Threshold calibration**: Adaptive thresholds per security based on individual liquidity profiles — a volume spike on Safaricom (high liquidity) means something different than the same spike on a low-cap USE counter.

### 3.3 NLP — Financial Sentiment (Planned)

**Scope**: East African financial news, NSE company announcements, regulatory filings

**Approach**: Fine-tune a multilingual BERT variant (Afriberta or AfriBERTa-large) on East African financial text. Standard FinBERT is trained on US financial news and performs poorly on regional context.

**Output**: Sentiment score per company per day, integrated as feature into XGBoost forecasting model

---

## 4. Open Research Questions

These are the questions Vestora's real-world deployment is uniquely positioned to answer:

1. **Do standard technical indicators retain predictive value in thin emerging markets, or do they degrade to noise below a liquidity threshold?**
2. **Can cross-listing price divergence between USE and NSE dual-listed securities be predicted and exploited systematically?**
3. **Does sentiment from East African financial media provide incremental predictive lift over price/volume features alone?**
4. **How do BOU/CBK policy rate decisions propagate through equity prices on EAC exchanges, and at what lag?**
5. **Can Isolation Forest reliably distinguish genuine corporate events from manipulation in a market with limited regulatory enforcement history?**

---

## 5. Evaluation Framework

All models are evaluated under the following constraints:

- **No look-ahead bias**: Strict walk-forward validation with 252-day (1 trading year) initial training window
- **Transaction cost adjustment**: Signal evaluation includes realistic spread and commission estimates for NSE
- **Benchmark comparison**: All models compared against naive baseline (random walk) and simple moving average crossover
- **Out-of-sample testing**: Final evaluation on held-out 2024–2025 data not used in any training or feature selection

---

## 6. Publication Potential

The combination of (a) novel application domain, (b) real deployment data, and (c) rigorous evaluation methodology positions this work for submission to:

- *African Journal of Management*
- *Emerging Markets Review* (Elsevier)
- ICLR Africa workshop tracks
- NeurIPS workshop on ML for developing economies

A well-documented research note on thin-market anomaly detection with real Vestora deployment data would be a strong EPFL MSc/PhD application supplement.

---

*Last updated: June 2026*
