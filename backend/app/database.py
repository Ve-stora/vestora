"""
Vestora Database Configuration
================================
Supports SQLite for local dev, PostgreSQL for production.

Two session flavors are exposed because the codebase has two active layers:
  - Sync  (get_db / SessionLocal): used by the NSE pipeline, the market
    data routes, and anything built on plain SQLAlchemy `Session`.
  - Async (get_async_db / AsyncSessionLocal): used by auth, portfolio,
    analytics, and b2b routes, which are built on `AsyncSession`.

Both point at the same physical database — for SQLite that's one file on
disk, for Postgres one connection string — just via two different DBAPI
drivers (pysqlite vs aiosqlite, psycopg2 vs asyncpg). This is a real
production-viable pattern for SQLAlchemy 2.0 while the async migration
finishes; it isn't a hack.
"""

import os
import uuid
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.types import CHAR, TypeDecorator
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

# ── Sync configuration (existing pipeline / market routes) ─────────────────

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./vestora_dev.db",  # local dev default
)

connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class GUID(TypeDecorator):
    """
    Platform-independent UUID type.

    Uses PostgreSQL's native UUID type when available, otherwise stores
    as a 36-character stringified hex value (SQLite, MySQL, etc). Models
    previously used `sqlalchemy.dialects.postgresql.UUID` directly, which
    fails at the driver level on any non-Postgres backend — that broke
    every table with a UUID primary key (User, Portfolio) under the
    SQLite dev DB. Lives here (not app/utils) so importing it from a
    model can never trigger app/utils/__init__.py's import chain, which
    would circle back through services.auth into models.user.
    """

    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name == "postgresql":
            return str(value)
        if not isinstance(value, uuid.UUID):
            return str(uuid.UUID(value))
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if isinstance(value, uuid.UUID):
            return value
        return uuid.UUID(value)


def get_db():
    """FastAPI dependency: yields a sync DB session, closes on exit."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Async configuration (auth / portfolio / analytics / b2b) ───────────────
# Derived from DATABASE_URL by swapping in an async driver, so both layers
# always point at the same database without needing two env vars.

def _to_async_url(sync_url: str) -> str:
    if sync_url.startswith("sqlite:///"):
        return sync_url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
    if sync_url.startswith("postgresql://"):
        return sync_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if sync_url.startswith("postgresql+psycopg2://"):
        return sync_url.replace("postgresql+psycopg2://", "postgresql+asyncpg://", 1)
    # Already async, or an unrecognized dialect — pass through unchanged.
    return sync_url


ASYNC_DATABASE_URL = os.getenv("ASYNC_DATABASE_URL", _to_async_url(DATABASE_URL))

async_engine = create_async_engine(ASYNC_DATABASE_URL, pool_pre_ping=True)

AsyncSessionLocal = async_sessionmaker(
    async_engine, class_=AsyncSession, expire_on_commit=False
)


async def get_async_db():
    """FastAPI dependency: yields an async DB session, closes on exit."""
    async with AsyncSessionLocal() as session:
        yield session


# ── Schema creation ──────────────────────────────────────────────────────

def init_db():
    """Create all tables. Call once at startup. Idempotent."""
    # Import every model module so SQLAlchemy's metadata registry is
    # complete before create_all() — see app/models/__init__.py.
    import app.models  # noqa: F401

    Base.metadata.create_all(bind=engine)