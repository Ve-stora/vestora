```markdown
# Contributing to Vestora

Thank you for your interest in contributing to **Vestora** — the open-source AI market intelligence platform for East African capital markets! 🎉

We welcome contributions from developers, quants, researchers, data engineers, designers, and writers.

## Code of Conduct

Be respectful, inclusive, and constructive. We follow the [Contributor Covenant](https://www.contributor-covenant.org/).

## How to Get Started

1. **Fork & Clone**
   ```bash
   git clone https://github.com/Ve-stora/vestora.git
   cd vestora
   ```

2. **Local Development (Recommended)**
   ```bash
   docker compose up --build
   ```
   - Frontend: http://localhost:5173
   - Backend + API docs: http://localhost:8000/docs

   See [docs/vestora-setup.md](docs/vestora-setup.md) for detailed setup, environment variables, and manual installation.

3. **Development Workflow**
   - Create a branch: `git checkout -b feature/your-feature-name` or `fix/issue-123`
   - Make changes
   - Test locally
   - Commit with clear messages (Conventional Commits recommended)
   - Push and open a Pull Request

## Types of Contributions

### High-Impact Areas (Great for Serious Contributors)
- **Quant/ML Research** (`/ml/`)
  - Improve XGBoost forecasting for thin markets
  - Better feature engineering or new anomaly detection approaches
  - Backtesting frameworks
  - Research on active questions (see [docs/research-methodology.md](docs/research-methodology.md))

- **Backend** (`/backend/`)
  - New API endpoints, data pipelines, authentication improvements

- **Frontend** (`/frontend/`)
  - Dashboard polish, new visualizations, mobile responsiveness

- **Data & Infrastructure**
  - NSE/USE data scrapers & normalization
  - CI/CD pipelines
  - Testing & evaluation frameworks

- **Documentation & Research**
  - Expand research methodology
  - Add tutorials or example notebooks
  - Translate docs

- **Non-code**: Bug reports, feature ideas, UI/UX feedback, blog posts

## Issue & PR Guidelines

- **Before opening a PR**: Create or comment on an issue first for discussion.
- Use clear titles and descriptions.
- Link related issues.
- Add tests where applicable.
- Update documentation if needed.

## Good First Issues
Look for issues labeled **`good first issue`** or **`help wanted`**.

## Recognition

All contributors will be:
- Added to the README "Contributors" section
- Mentioned in release notes
- Able to use the project in portfolios/academic work

## Questions?

- Open a GitHub Discussion
- Email: veritasndiema@gmail.com
- Or reach out on LinkedIn (Keith Ndiema)

**Together we can build the intelligence layer Africa’s capital markets deserve.** 🌍
```

### 2. Sample Announcement Post (for X/Twitter, LinkedIn, etc.)

**Short version (X/Twitter):**
```
Just open-sourced Vestora — AI-powered market intelligence for East Africa’s capital markets (starting with NSE Kenya).

XGBoost forecasting, anomaly detection for thin markets, portfolio analytics, and more. Built as the “intelligence layer” on top of Ziidi Trader and other execution platforms.

Looking for serious contributors:
• Quants / ML engineers
• Data pipeline folks
• React frontend devs
• Researchers interested in emerging market finance

Docker setup in <2 mins. Real problem, real data, real impact.

Repo: https://github.com/Ve-stora/vestora

RTs & contributions appreciated! #QuantFinance #AfricaTech #OpenSource #NSEKenya
```

**Longer version (LinkedIn or dev.to/HN post):**
```
Excited to share **Vestora** — an open-source AI market intelligence platform built for Africa’s democratizing capital markets.

After Ziidi Trader made trading accessible via M-PESA, millions of new investors still lack professional-grade analytics. Vestora fills that gap with:
- Price forecasting tailored to low-liquidity NSE equities
- Anomaly detection calibrated for emerging markets
- Sentiment from local financial media
- Portfolio risk tools

Tech: FastAPI + React + XGBoost + PostgreSQL + Docker

It’s early stage but fully runnable locally. I’m actively looking for collaborators — especially quants, ML engineers, and East Africa-focused developers.

Check it out, run it, and let’s build something meaningful: https://github.com/Ve-stora/vestora

Contributions, feedback, and stars welcome!
```
