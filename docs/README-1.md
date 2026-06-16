# Vestora Platform

**Pan-African Capital Markets Intelligence Layer — Starting with NSE**

Vestora delivers actionable market intelligence, price forecasting, anomaly detection, momentum signals, and macroeconomic context for East African equities, bonds, and beyond. Built as a complementary analytics layer on top of execution platforms like Ziidi Trader — where access is expanding faster than analytical tools.

> **Positioning**: Ziidi Trader (execution) · Hisa/Ndovu (portfolios) · **Vestora (intelligence & forecasting)**

---

## 🎯 Vision

To equip retail investors, diaspora, and small institutions with professional-grade intelligence for Africa's democratizing capital markets. Built in Uganda. Built for East Africa.

---

## ✨ Key Features (MVP)

- **Market Intelligence Dashboard** — Real-time and historical NSE data, expanding across EAC exchanges
- **AI Analytics Engine** — Price forecasting, anomaly detection, momentum signals, and macroeconomic context powered by custom XGBoost models trained on EAC market data with Isolation Forest anomaly detection
- **Portfolio Analytics** — Performance tracking, risk signals, and scenario modeling
- **Data API** — Structured, B2B-ready endpoints for broker and institutional integration

---

## 🛠 Tech Stack

- **Backend**: FastAPI + Python + SQLAlchemy + JWT
- **Frontend**: React + TypeScript + Vite + Tailwind CSS
- **Database**: PostgreSQL (SQLite for local dev)
- **AI/ML**: Custom forecasting models (XGBoost + Isolation Forest) + Groq/OpenAI compatible LLM layer
- **Containerization**: Docker + Docker Compose

---

## 🚀 Quick Start

See `docs/setup.md` for full configuration details.

```bash
git clone https://github.com/Ve-stora/vestora-platform.git
cd vestora-platform
docker-compose up --build
```

| Service | URL |
|---|---|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| Health Check | http://localhost:8000/health |

---

## 📸 Screenshots

> Dashboard, analytics, and portfolio views — coming with v0.2.0 release.

---

## 📈 Market Focus

### Phase 1: NSE (Active)

- **Primary Exchange**: Nairobi Securities Exchange — 60+ listed companies, millions USD daily liquidity
- **Opportunity**: 1.4M+ retail investors newly activated via Ziidi Trader need analytical intelligence, not another trading interface
- **Data Infrastructure**: Robust scraping and normalization pipelines targeting structured NSE data feeds

### Expansion Roadmap

See `docs/roadmap.md` for full detail.

| Phase | Timeline | Scope |
|---|---|---|
| 1 | Now – End 2026 | NSE depth — equities, bonds, T-bills |
| 2 | Early 2027 | USE (Uganda Securities Exchange) |
| 3 | Mid 2027 | DSE (Tanzania) + RSE (Rwanda) |
| 4 | 2028+ | Pan-African: GSE (Ghana), NGX (Nigeria) |

---

## 💰 Revenue Model

1. **B2B API Licensing** *(primary)* — White-label analytics for brokers, SACCOs, microfinance institutions, and small fund managers who need structured intelligence without Bloomberg pricing
2. **Premium Retail Subscriptions** — Advanced signals, forecasting reports, and portfolio risk analysis for individual investors
3. **Data Partnerships** — Aggregated, anonymized market intelligence for development finance institutions, researchers, and media (FSD Africa, UNCDF, financial press)

---

## ⚖️ Legal Posture

Vestora is a **data and analytics platform** — not an investment advisor. All outputs are framed as data observations and model outputs:

- *"Historical patterns indicate..."*
- *"Model forecast based on 90-day rolling data..."*
- *"Anomaly detected in trading volume relative to 30-day baseline..."*

No buy/sell recommendations. No personalized financial advice. This mirrors the Bloomberg/Reuters data-vendor model and operates outside CMA Kenya advisory licensing requirements.

---

## 👥 Target Users

| Segment | Description |
|---|---|
| **Primary** | NSE retail investors activated by Ziidi Trader — have execution, need intelligence |
| **Secondary** | East African diaspora seeking informed regional market exposure |
| **Tertiary** | Small institutions (SACCOs, microfinance, boutique funds) needing affordable structured data |

---

## 📚 Research Methodology

Vestora's ML components address genuinely underexplored territory:

- **Price forecasting in thin emerging markets** — applying XGBoost ensemble methods to low-liquidity EAC equities
- **Anomaly detection** — Isolation Forest applied to volume and price irregularities on markets with infrequent trading
- **NLP on East African financial news** — sentiment and event extraction from regional financial media

See `docs/research-methodology.md` for data sources, model architecture, and evaluation methodology.

---

## 📁 Project Structure

```
vestora-platform/
├── backend/              # FastAPI backend — market data, auth, ML inference
├── frontend/             # React + TypeScript dashboard
├── docs/                 # Roadmap, research methodology, API framing, data sources
├── docker-compose.yml
└── README.md
```

---

## 📡 Key API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/auth/register` | Create account |
| POST | `/api/auth/login` | Authenticate |
| GET | `/api/market/stocks` | NSE market data |
| GET | `/api/market/forecast/{symbol}` | Price forecast for symbol |
| POST | `/api/ai/analytics` | Analytics query engine |
| GET | `/api/portfolio` | Portfolio performance |

Full API documentation available at `/docs` when running locally.

---

## 📄 Documentation

- [`docs/roadmap.md`](docs/roadmap.md) — Phased EAC expansion plan
- [`docs/research-methodology.md`](docs/research-methodology.md) — ML architecture and data methodology
- [`docs/data-sources.md`](docs/data-sources.md) — Data origins, cleaning pipeline, update frequency
- [`docs/api-framing.md`](docs/api-framing.md) — Legal-safe output templates for all analytics endpoints
- [`docs/setup.md`](docs/setup.md) — Full local development setup

---

**Contact**: veritasndiema@gmail.com · [LinkedIn](https://ug.linkedin.com/in/keith-ndiema-292k25)

**License**: MIT

---

*Built in Uganda. Built for East Africa's capital markets.*
