#!/usr/bin/env bash
# Vestora Quick Start
# Gets the full platform running in one shot.

set -e

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Vestora — NSE Intelligence Platform"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# ── Python setup ───────────────────────────────────────
cd backend
if [ ! -d ".venv" ]; then
  echo "→ Creating Python virtualenv..."
  python3 -m venv .venv
fi

source .venv/bin/activate
echo "→ Installing Python dependencies..."
pip install -q -r ../requirements-minimal.txt

# ── DB seed ─────────────────────────────────────────────
echo "→ Seeding NSE data (180-day history for 20 stocks)..."
cd ..
python data/seeds/seed_nse.py

# ── ML training ─────────────────────────────────────────
echo "→ Training XGBoost forecasters + anomaly detectors..."
python -m ml.training.train_all --min-days 60
echo "   ML models trained and saved to ml/models/saved/"

# ── Frontend setup ──────────────────────────────────────
if [ -d "frontend" ]; then
  echo "→ Installing frontend dependencies..."
  cd frontend
  npm install --silent
  cd ..
fi

# ── Launch ──────────────────────────────────────────────
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Starting Vestora..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  Backend API → http://localhost:8000"
echo "  API Docs    → http://localhost:8000/docs"
echo "  Frontend    → http://localhost:5173"
echo ""

# Start backend
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Start frontend if it exists
if [ -d "../frontend" ]; then
  cd ../frontend && npm run dev &
  FRONTEND_PID=$!
fi

echo "  Backend PID: $BACKEND_PID"
echo "  Press Ctrl+C to stop all services"
echo ""

wait
