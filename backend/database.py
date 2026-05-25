"""Flora Platform — Async SQLAlchemy Database Setup"""
from __future__ import annotations

import logging
from typing import AsyncGenerator

from sqlalchemy import create_engine, event, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from backend.config import settings

logger = logging.getLogger(__name__)

# Build async database URL (convert postgresql:// to postgresql+asyncpg:// etc.)
DATABASE_URL = settings.DATABASE_URL
ASYNC_DATABASE_URL = DATABASE_URL

# Simple conversion for common drivers
if ASYNC_DATABASE_URL.startswith("sqlite:///"):
    # aiosqlite for SQLite async support
    ASYNC_DATABASE_URL = ASYNC_DATABASE_URL.replace("sqlite:///", "sqlite+aiosqlite:///")
elif ASYNC_DATABASE_URL.startswith("postgresql://"):
    ASYNC_DATABASE_URL = ASYNC_DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
elif ASYNC_DATABASE_URL.startswith("mysql://"):
    ASYNC_DATABASE_URL = ASYNC_DATABASE_URL.replace("mysql://", "mysql+aiomysql://")

logger.info("Async database URL: %s", ASYNC_DATABASE_URL.split("@")[-1] if "@" in ASYNC_DATABASE_URL else ASYNC_DATABASE_URL)

# Async engine (primary — used everywhere at runtime)
async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=settings.DB_ECHO,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_pre_ping=True,
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Sync engine/migrations (Alembic) — also expose SessionLocal for legacy/sync code
sync_url = DATABASE_URL
if sync_url.startswith("sqlite+aiosqlite:///"):
    sync_url = sync_url.replace("sqlite+aiosqlite:///", "sqlite:///")
sync_engine = create_engine(sync_url, echo=settings.DB_ECHO)
SessionLocal = sessionmaker(bind=sync_engine, expire_on_commit=False)


# ─── Table Creation ──────────────────────────────────────────────────
async def create_all_tables() -> None:
    """Create all tables (development convenience — Alembic preferred in prod)."""
    from backend.models.base import Base  # noqa: F811
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("All database tables created (async)")


async def drop_all_tables() -> None:
    """Drop all tables (development/testing only)."""
    from backend.models.base import Base  # noqa: F811
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    logger.info("All database tables dropped (async)")


# ─── Session Dependency ──────────────────────────────────────────────
async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async database session for FastAPI dependency injection."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ─── Health Check ────────────────────────────────────────────────────
async def check_db_health() -> bool:
    """Alias for health checks."""
    return await check_db_connection()


async def check_db_connection() -> bool:
    """Verify the database connection is alive."""
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error("Database connection check failed: %s", e)
        return False
