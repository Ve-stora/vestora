from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.database import init_db, AsyncSessionLocal
from app.api import auth, market, portfolio, analytics, b2b
from app.config import settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ──────────────────────────────────────────────────────────────
    logger.info("Vestora starting up — env=%s", settings.APP_ENV)

    # 1. Create DB tables
    await init_db()
    logger.info("Database tables initialised")

    # 2. Seed metadata (NSE symbols) — idempotent, skips existing records
    async with AsyncSessionLocal() as db:
        from app.db_seed import seed_database
        await seed_database(db)

    logger.info("Vestora ready — API available")
    yield

    # ── Shutdown ─────────────────────────────────────────────────────────────
    logger.info("Vestora shutting down")


app = FastAPI(
    title="Vestora API",
    description=(
        "Pan-African Capital Markets Intelligence Layer. "
        "Market data analytics for NSE, USE, and EAC exchanges. "
        "Not investment advice."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth.router,      prefix="/api/auth",      tags=["Auth"])
app.include_router(market.router,    prefix="/api/market",    tags=["Market"])
app.include_router(portfolio.router, prefix="/api/portfolio", tags=["Portfolio"])
app.include_router(analytics.router, prefix="/api/ai",        tags=["Analytics"])
app.include_router(b2b.router,       prefix="/api/b2b",       tags=["B2B"])


# ── Health ────────────────────────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
async def health():
    return {
        "status":   "ok",
        "platform": "Vestora",
        "version":  "0.1.0",
        "exchange": "NSE Phase 1",
    }