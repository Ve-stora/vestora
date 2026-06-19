# Vestora — Project Setup Commands

Open VS Code terminal (`Ctrl+` `` ` ``) and run these top to bottom.


## 1. Create root and navigate

```bash
mkdir vestora && cd vestora
```

## 2. Create folder structure

```bash
mkdir -p \
  backend/app/{api,models,schemas,services,ml,utils} \
  backend/tests \
  frontend/src/{components/{dashboard,market,portfolio,analytics,shared},pages,hooks,services,store,types} \
  ml/{notebooks,models,data} \
  data/{pipeline,seeds} \
  docs
```


## 3. Create all files

```bash
touch \
  backend/app/__init__.py \
  backend/app/main.py \
  backend/app/config.py \
  backend/app/database.py \
  backend/app/dependencies.py \
  backend/app/api/__init__.py \
  backend/app/api/auth.py \
  backend/app/api/market.py \
  backend/app/api/portfolio.py \
  backend/app/api/analytics.py \
  backend/app/api/b2b.py \
  backend/app/models/__init__.py \
  backend/app/models/user.py \
  backend/app/models/stock.py \
  backend/app/models/portfolio.py \
  backend/app/models/forecast.py \
  backend/app/schemas/__init__.py \
  backend/app/schemas/auth.py \
  backend/app/schemas/market.py \
  backend/app/schemas/portfolio.py \
  backend/app/schemas/analytics.py \
  backend/app/services/__init__.py \
  backend/app/services/auth.py \
  backend/app/services/scraper.py \
  backend/app/services/market.py \
  backend/app/services/forecasting.py \
  backend/app/services/anomaly.py \
  backend/app/services/portfolio.py \
  backend/app/ml/__init__.py \
  backend/app/ml/xgboost_model.py \
  backend/app/ml/isolation_forest.py \
  backend/app/ml/feature_engineering.py \
  backend/app/ml/evaluation.py \
  backend/app/utils/__init__.py \
  backend/app/utils/auth.py \
  backend/app/utils/cache.py \
  backend/app/utils/framing.py \
  backend/tests/__init__.py \
  backend/tests/test_auth.py \
  backend/tests/test_market.py \
  backend/tests/test_ml.py \
  backend/requirements.txt \
  backend/Dockerfile \
  backend/.env.example \
  frontend/src/main.tsx \
  frontend/src/App.tsx \
  frontend/src/services/api.ts \
  frontend/src/services/websocket.ts \
  frontend/src/store/AuthContext.tsx \
  frontend/src/types/index.ts \
  frontend/src/pages/Dashboard.tsx \
  frontend/src/pages/Market.tsx \
  frontend/src/pages/Portfolio.tsx \
  frontend/src/pages/Analytics.tsx \
  frontend/src/pages/Login.tsx \
  frontend/src/components/shared/ProtectedRoute.tsx \
  frontend/src/hooks/useMarketData.ts \
  frontend/src/hooks/usePortfolio.ts \
  frontend/src/hooks/useAuth.ts \
  data/seeds/nse_symbols.json \
  docker-compose.yml \
  .env.example \
  .gitignore \
  LICENSE \
  README.md
```


## 4. Verify structure

```bash
find . -type f | sort
```

Expected output — every file listed alphabetically. Should be 50+ files across backend, frontend, data, and root.


## 5. Open in VS Code

```bash
code .
```


## After This

Start copy-pasting in this order — each file depends on the previous:

1. `backend/app/config.py`
2. `backend/app/database.py`
3. `backend/app/models/user.py`
4. `backend/app/models/stock.py`
5. `backend/app/models/forecast.py`
6. `backend/app/main.py`
7. `backend/app/api/auth.py`
8. `backend/app/api/market.py`
9. `backend/app/api/analytics.py`
10. `backend/app/api/b2b.py`
11. `backend/app/ml/xgboost_model.py`
12. `backend/app/ml/isolation_forest.py`
13. `backend/app/services/scraper.py`
14. `backend/requirements.txt`
15. `backend/Dockerfile`
16. `docker-compose.yml`
17. `.env.example` → copy to `.env` and fill in keys
18. `.gitignore`
19. `frontend/src/types/index.ts`
20. `frontend/src/services/api.ts`
21. `frontend/src/App.tsx`
22. `data/seeds/nse_symbols.json`
23. `README.md`


## Install Dependencies (after pasting requirements.txt)

**Backend**
```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**Frontend** (run Vite scaffold first if package.json doesn't exist yet)
```bash
cd frontend
npm create vite@latest . -- --template react-ts
npm install
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
npm install react-router-dom recharts lucide-react
```


## Run Without Docker (dev)

**Terminal 1 — Backend**
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

**Terminal 2 — Frontend**
```bash
cd frontend
npm run dev
```


## Run With Docker

```bash
docker compose up --build
```

| Service | URL |
|---|---|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| Health | http://localhost:8000/health |
