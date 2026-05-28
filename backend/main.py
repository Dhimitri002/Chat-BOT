"""
Flora Platform — FastAPI Backend Entry Point
==============================================

Production-ready FastAPI application with:
- CORS, security headers, rate limiting, request logging
- All API routes via centralized router
- Automatic database table creation on startup
- Health check and root endpoints
- Background health monitoring loop
- Request metrics collection
"""
from __future__ import annotations

import asyncio
import logging

from fastapi import FastAPI
from loguru import logger

from backend.api.router import api_router
from backend.config import settings
from backend.core.middleware import setup_security_middleware
from backend.database import check_db_connection, create_all_tables
from monitoring.middleware import MetricsMiddleware
from monitoring.health import monitor_loop

logging.basicConfig(level=logging.INFO)

# ─── App Instance ────────────────────────────────────────────────────────────
app = FastAPI(
    title="Flora Platform API",
    description="API da Plataforma Flora — Chatbots WhatsApp com IA",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ─── Middleware (order matters) ───────────────────────────────────────────────
# Registration order is reverse of execution order:
#   First registered = outermost (runs first on request, last on response)
setup_security_middleware(app)
app.add_middleware(MetricsMiddleware)

# ─── API Routes ────────────────────────────────────────────────────────────────
app.include_router(api_router)


# ─── Lifecycle Events ─────────────────────────────────────────────────────────

@app.on_event("startup")
async def startup_event():
    """Initialize database and services on startup."""
    logger.info("🌸 Flora Platform starting up...")
    try:
        await create_all_tables()
        logger.info("✅ Database tables created/verified")
    except Exception as e:
        logger.warning(f"⚠️ Database table creation issue: {e}")

    db_ok = await check_db_connection()
    if db_ok:
        logger.info("✅ Database connection verified")
    else:
        logger.warning("⚠️ Database connection failed — check DATABASE_URL")

    # Start background health monitor (non-blocking)
    interval = getattr(settings, "HEALTH_CHECK_INTERVAL_SECONDS", 60)
    asyncio.create_task(monitor_loop(interval_seconds=interval))
    logger.info(f"🔍 Health monitor started (interval: {interval}s)")

    logger.info("🌸 Flora Platform ready!")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("🌸 Flora Platform shutting down...")


# ─── Root Endpoint ─────────────────────────────────────────────────────────────

@app.get("/", tags=["root"])
async def root():
    return {
        "name": "Flora Platform",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/v1/health",
    }
