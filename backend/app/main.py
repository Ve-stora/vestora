from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.database import init_db
from app.api import auth, market, portfolio, analytics, b2b
from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    yield
    # Shutdown — cleanup if needed


app = FastAPI(
    title="Vestora API",
    description="Pan-African Capital Markets Intelligence Layer",
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

# Routers
app.include_router(auth.router,      prefix="/api/auth",      tags=["Auth"])
app.include_router(market.router,    prefix="/api/market",    tags=["Market"])
app.include_router(portfolio.router, prefix="/api/portfolio", tags=["Portfolio"])
app.include_router(analytics.router, prefix="/api/ai",        tags=["Analytics"])
app.include_router(b2b.router,       prefix="/api/b2b",       tags=["B2B"])


@app.get("/health")
async def health():
    return {"status": "ok", "platform": "Vestora", "version": "0.1.0"}