"""
Flora Platform — FastAPI Backend Entry Point
"""
from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from backend.api.router import api_router
from backend.config import settings
from backend.database import check_db_connection, create_all_tables

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="Flora Platform API",
    description="API da Plataforma Flora — Chatbots WhatsApp com IA",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all API routes
app.include_router(api_router)


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

    logger.info("🌸 Flora Platform ready!")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("🌸 Flora Platform shutting down...")


@app.get("/", tags=["root"])
async def root():
    return {
        "name": "Flora Platform",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/v1/health",
    }
