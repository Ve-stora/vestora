#!/usr/bin/env bash
# Vestora Quick Start
# Gets the full platform running locally (no Docker) in one shot.

set -uo pipefail  # NOTE: no -e — steps are checked individually so one
                  # failure (e.g. seeding) doesn't kill the whole script.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

BACKEND_PID=""
FRONTEND_PID=""

info()  { echo "→ $1"; }
warn()  { echo "⚠ $1"; }
error() { echo "✗ $1" >&2; }
ok()    { echo "✓ $1"; }

cleanup() {
  echo ""
  info "Shutting down..."
  [ -n "$BACKEND_PID" ]  && kill "$BACKEND_PID"  2>/dev/null
  [ -n "$FRONTEND_PID" ] && kill "$FRONTEND_PID" 2>/dev/null
  wait 2>/dev/null
}
trap cleanup EXIT INT TERM

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Vestora — NSE Intelligence Platform"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# ── Prerequisite checks ─────────────────────────────────
if ! command -v python3 &>/dev/null; then
  error "Python 3 not found. Install Python 3.11+ and re-run."
  exit 1
fi
if ! command -v npm &>/dev/null; then
  error "npm not found. Install Node.js 20+ and re-run."
  exit 1
fi

# ── Python venv + deps (backend/) ───────────────────────
cd "$ROOT_DIR/backend"

if [ ! -d ".venv" ]; then
  info "Creating Python virtualenv..."
  python3 -m venv .venv || { error "Failed to create virtualenv"; exit 1; }
fi

# shellcheck disable=SC1091
source .venv/bin/activate

REQ_FILE="requirements-minimal.txt"
REQ_STAMP=".venv/.requirements_installed"

if [ ! -f "$REQ_STAMP" ] || [ "$REQ_FILE" -nt "$REQ_STAMP" ]; then
  info "Installing Python dependencies..."
  pip install -q --upgrade pip
  if pip install -q -r "$REQ_FILE"; then
    touch "$REQ_STAMP"
    ok "Python dependencies installed."
  else
    error "Failed to install Python dependencies (see output above)."
    exit 1
  fi
else
  ok "Python dependencies already up to date."
fi

cd "$ROOT_DIR"

# ── DB seed (non-fatal) ──────────────────────────────────
info "Seeding NSE data (180-day history for 20 stocks)..."
if python data/seeds/seed_nse.py; then
  ok "NSE data seeded."
else
  warn "Seeding failed — continuing without seed data. The API will still start."
fi

# ── ML training (non-fatal) ──────────────────────────────
info "Training XGBoost forecasters + anomaly detectors..."
if (cd "$ROOT_DIR/backend/app" && python -m ml.training.train_all --min-days 60); then
  ok "ML models trained and saved to backend/app/ml/models/saved/"
else
  warn "ML training failed — continuing without trained models. Forecast endpoints may be degraded."
fi

# ── Frontend deps ────────────────────────────────────────
if [ -d "$ROOT_DIR/frontend" ]; then
  cd "$ROOT_DIR/frontend"
  if [ ! -d "node_modules" ] || [ "package.json" -nt "node_modules" ]; then
    info "Installing frontend dependencies..."
    npm install --silent || { error "npm install failed"; exit 1; }
  else
    ok "Frontend dependencies already up to date."
  fi
  cd "$ROOT_DIR"
fi

# ── Launch ────────────────────────────────────────────────
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Starting Vestora..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  Backend API → http://localhost:8000"
echo "  API Docs    → http://localhost:8000/docs"
echo "  Frontend    → http://localhost:5173"
echo ""

cd "$ROOT_DIR/backend"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd "$ROOT_DIR"

if [ -d "$ROOT_DIR/frontend" ]; then
  cd "$ROOT_DIR/frontend"
  npm run dev &
  FRONTEND_PID=$!
  cd "$ROOT_DIR"
fi

echo "  Backend PID: $BACKEND_PID"
[ -n "$FRONTEND_PID" ] && echo "  Frontend PID: $FRONTEND_PID"
echo "  Press Ctrl+C to stop all services"
echo ""

wait