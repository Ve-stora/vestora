# Vestora

### The intelligence layer for Africa's capital markets.

Execution platforms enable trading. **Vestora enables understanding.**

Vestora is an AI-powered market intelligence platform delivering price forecasting, anomaly detection, momentum signals, and macroeconomic context for East African equities, bonds, and beyond — built as a complementary analytics layer on top of execution platforms like Ziidi Trader, where access is expanding faster than analytical tools.

> **Built for Africa 🌍**



## The Problem

Africa's capital markets are opening up fast. Retail participation is growing. Mobile-first execution is here.

But professional-grade analytical tools? Still locked behind Bloomberg terminals that cost $24,000/year — or simply nonexistent for emerging markets like NSE, USE, and DSE.

The result: millions of investors making decisions with no data infrastructure beneath them.



## Why Now

In early 2026, Safaricom and NSE launched Ziidi Trader — embedding share trading directly into M-PESA. On day one, over half of all NSE orders were placed through M-PESA. 1.4 million registered NSE investors now have frictionless execution.

They have access. They don't have intelligence.

That's the gap Vestora fills.



## Positioning

| Layer | Platform |
|---|---|
| Execution | Ziidi Trader · stockbrokers |
| Portfolio management | Hisa · Ndovu |
| **Intelligence & forecasting** | **Vestora** |

Vestora is not competing with execution or portfolio platforms. It sits above them as the analytical layer that makes every trade more informed.



## Vision

To equip retail investors, diaspora, and small institutions with professional-grade intelligence for Africa's democratizing capital markets — where access is expanding faster than analytical tools.



## ✨ Core Capabilities

**Market Intelligence Dashboard**
Real-time and historical NSE data. Market movers, sector performance, corporate actions, and event tracking — expanding across African exchanges.

**AI Analytics Engine**
Price forecasting built on custom XGBoost models trained on African market data. Isolation Forest anomaly detection calibrated for thin, low-liquidity emerging markets. Momentum and trend signals. Sentiment analysis from East African financial media.

**Portfolio Analytics**
Performance tracking, risk and concentration analysis, scenario modeling, and historical benchmarking against NSE indices.

**Data API**
Structured, B2B-ready endpoints for brokers, SACCOs, and institutions that need analytics infrastructure without building it themselves.



## Tech Stack

| Layer | Technologies |
|---|---|
| **Backend** | FastAPI · Python · SQLAlchemy · JWT |
| **Frontend** | React · TypeScript · Vite · Tailwind CSS |
| **Database** | PostgreSQL · SQLite (local dev) |
| **AI/ML** | XGBoost · Isolation Forest · Groq/OpenAI-compatible LLM |
| **Infrastructure** | Docker · Docker Compose |



## 🏗 Architecture

```
Market Data Sources (NSE, CBK, African stock exchanges)
              │
              ▼
   Data Pipeline & Normalization
              │
              ▼
      PostgreSQL Data Layer
              │
    ┌─────────┼─────────┐
    ▼         ▼         ▼
Forecasting  Anomaly  Portfolio
 Engine     Detection  Engine
    └─────────┼─────────┘
              │
              ▼
       FastAPI Backend
              │
       ┌──────┴──────┐
       ▼             ▼
React Dashboard   B2B API
```



## Quick Start

**Prerequisites**: Python 3.11+ · Node.js 20+ · Docker

```bash
git clone https://github.com/Ve-stora/vestora.git
cd vestora
docker compose up --build
```

| Service | URL |
|---|---|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| Health Check | http://localhost:8000/health |

See [`docs/setup.md`](docs/setup.md) for full configuration.



## 📸 Screenshots

> Dashboard, analytics, and portfolio views — coming with v0.2.0 release.



## 📈 Market Focus

### Phase 1: NSE (Active)

- **Primary Exchange**: Nairobi Securities Exchange — 60+ listed companies, millions USD daily liquidity
- **Opportunity**: 1.4M+ retail investors newly activated via Ziidi Trader need analytical intelligence, not another trading interface
- **Data Infrastructure**: Robust scraping and normalization pipelines targeting structured NSE data feeds

### Expansion Roadmap

| Phase | Timeline | Scope |
|---|---|---|
| **1 — NSE** | Now – End 2026 | Equities, bonds, T-bills. First B2B clients. |
| **2 — USE** | Early 2027 | Uganda. Cross-market analytics. Diaspora features. |
| **3 — DSE + RSE** | Mid 2027 | Tanzania + Rwanda. East African unified layer. |
| **4 — Pan-African** | 2028+ | GSE, NGX, JSX Institutional APIs. Series A. |

Full detail: [`docs/roadmap.md`](docs/roadmap.md)



## Revenue Model

**B2B API Licensing** *(primary)*
White-label analytics for brokers, SACCOs, microfinance institutions, and boutique fund managers who need structured intelligence without Bloomberg pricing.

**Premium Retail Subscriptions**
Advanced signals, forecasting reports, and portfolio risk analysis for individual investors.

**Data Partnerships**
Aggregated, anonymized market intelligence for development finance institutions, researchers, and financial media (FSD Africa, UNCDF, regional press).



## 👥 Who It's For

| Segment | Description |
|---|---|
| **Retail investors** | NSE participants activated by Ziidi Trader — have execution, need intelligence |
| **Diaspora investors** | East Africans abroad seeking structured insight into regional markets |
| **Small institutions** | SACCOs, microfinance funds, boutique managers needing affordable data infrastructure |



## ⚖️ Legal Posture

Vestora is a **data and analytics platform** — not a licensed investment advisor.

All outputs are framed as data observations and model results:

- *"Historical patterns indicate..."*
- *"Model forecast based on 90-day rolling data..."*
- *"Anomaly detected in trading volume relative to 30-day baseline..."*

No buy/sell recommendations. No personalized financial advice. This mirrors the Bloomberg/Reuters data-vendor model and operates outside CMA Kenya advisory licensing requirements.

See [`docs/api-framing.md`](docs/api-framing.md) for compliant output templates.



## 📚 Research

Vestora's ML components address genuinely underexplored territory in computational finance:

- **Price forecasting in thin emerging markets** — applying XGBoost ensemble methods to low-liquidity EAC equities where deep learning assumptions break down
- **Anomaly detection** — Isolation Forest calibrated for markets with infrequent trading and limited regulatory enforcement history
- **NLP on African financial news** — sentiment and event extraction from regional media, not US/EU financial corpora

**Active research questions:**
- Do standard technical indicators retain predictive value below a liquidity threshold?
- Can cross-listing price divergence between USE and NSE dual-listed securities be predicted systematically?
- Does sentiment from African financial media provide incremental predictive lift over price/volume features alone?

See [`docs/research-methodology.md`](docs/research-methodology.md) for data sources, model architecture, and evaluation methodology.



## 📡 Core API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/auth/register` | Create account |
| POST | `/api/auth/login` | Authenticate |
| GET | `/api/market/stocks` | NSE market data |
| GET | `/api/market/forecast/{symbol}` | Price forecast for symbol |
| POST | `/api/ai/analytics` | Analytics query engine |
| GET | `/api/portfolio` | Portfolio performance |

Full API documentation at `/docs` when running locally.



## 📁 Project Structure

```
vestora-platform/
├── backend/              # FastAPI backend — market data, auth, ML inference
├── frontend/             # React + TypeScript dashboard
├── docs/                 # Roadmap, research methodology, API framing, data sources
├── docker-compose.yml
└── README.md
```



## 📄 Documentation

| Doc | Description |
|---|---|
| [`docs/setup.md`](docs/setup.md) | Local development setup |
| [`docs/roadmap.md`](docs/roadmap.md) | Phased EAC expansion plan |
| [`docs/research-methodology.md`](docs/research-methodology.md) | ML architecture and evaluation |
| [`docs/data-sources.md`](docs/data-sources.md) | Data origins, pipeline, limitations |
| [`docs/api-framing.md`](docs/api-framing.md) | Legal-safe output templates |



**Contact**: veritasndiema@gmail.com · [LinkedIn](https://ug.linkedin.com/in/keith-ndiema-292k25) · [GitHub](https://github.com/Ve-stora/vestora)

**License**: AGPL-3.0



*Built by Keith Kissa Ndiema at Mbarara University of Science and Technology. Building the intelligence layer for Africa's capital markets.*