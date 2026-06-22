"""
Vestora Backend — FastAPI Application Entry Point
"""

import asyncio
import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import market as market_routes
from app.api import router as api_router          # auth, portfolio, analytics, market (old)
from app.database import SessionLocal, init_db    # was: app.core.database (doesn't exist)
from app.services.nse_pipeline import NSEPipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("vestora")

scheduler = AsyncIOScheduler(timezone="Africa/Nairobi")


async def run_scheduled_sync():
    """Daily NSE data sync — runs at 16:45 EAT (after NSE close at 15:30)."""
    logger.info("Scheduled NSE sync starting...")
    db = SessionLocal()
    try:
        async with NSEPipeline(db) as pipeline:
            result = await pipeline.run_full_sync()
        logger.info(f"Scheduled sync complete: {result}")
    except Exception as e:
        logger.error(f"Scheduled sync failed: {e}")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    logger.info("Database initialized")

    # Schedule daily sync: Mon–Fri at 16:45 EAT
    scheduler.add_job(
        run_scheduled_sync,
        CronTrigger(day_of_week="mon-fri", hour=16, minute=45, timezone="Africa/Nairobi"),
        id="nse_daily_sync",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("NSE sync scheduler started")

    yield

    # Shutdown
    scheduler.shutdown(wait=False)
    logger.info("Scheduler stopped")


app = FastAPI(
    title="Vestora API",
    description="Intelligence layer for East African capital markets.",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://vestora.africa"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the newer routes/market router (sync SQLAlchemy, NSEPipeline-backed)
app.include_router(market_routes.router)

# Mount the full API router (auth, portfolio, analytics, legacy market)
app.include_router(api_router)


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.2.0"}


@app.get("/")
async def root():
    return {
        "name": "Vestora API",
        "description": "Intelligence layer for East African capital markets",
        "docs": "/docs",
        "health": "/health",
    }