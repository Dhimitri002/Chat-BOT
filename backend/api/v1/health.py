"""Flora Platform — Health Check Endpoints"""
from __future__ import annotations

import os
import platform
import time
from datetime import datetime, timezone

import psutil
from fastapi import APIRouter, Depends
from sqlalchemy import text

from backend.database import async_engine, check_db_health
from backend.config import settings

router = APIRouter(tags=["health"])

# Track startup time
_STARTUP_TIME = time.time()


def _get_uptime_seconds() -> float:
    return round(time.time() - _STARTUP_TIME, 2)


def _get_system_info() -> dict:
    """Get real system information."""
    try:
        process = psutil.Process(os.getpid())
        mem_info = process.memory_info()
        return {
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "memory": {
                "rss_mb": round(mem_info.rss / (1024 * 1024), 2),
                "vms_mb": round(mem_info.vms / (1024 * 1024), 2),
                "percent": round(process.memory_percent(), 2),
            },
            "system": {
                "platform": platform.system(),
                "platform_version": platform.version(),
                "python_version": platform.python_version(),
                "cpu_count": psutil.cpu_count(),
                "total_memory_mb": round(psutil.virtual_memory().total / (1024 * 1024), 2),
            },
        }
    except Exception:
        return {
            "cpu_percent": None,
            "memory": {"rss_mb": None, "vms_mb": None, "percent": None},
            "system": {
                "platform": platform.system(),
                "platform_version": platform.version(),
                "python_version": platform.python_version(),
                "cpu_count": os.cpu_count(),
                "total_memory_mb": None,
            },
        }


async def _check_async_db() -> dict:
    """Check async database connectivity."""
    try:
        async with async_engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "healthy", "backend": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "backend": str(e)}


@router.get("/health", summary="Quick health check")
async def health_check():
    """Quick health check for load balancers."""
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": settings.APP_VERSION,
    }


@router.get("/health/detailed", summary="Detailed system health")
async def detailed_health():
    """Detailed health check with system info, DB status, and uptime."""
    db_health = await check_db_health()
    async_db = await _check_async_db()
    sys_info = _get_system_info()

    overall = "healthy"
    if db_health["status"] != "healthy" or async_db["status"] != "healthy":
        overall = "degraded"

    return {
        "status": overall,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "uptime_seconds": _get_uptime_seconds(),
        "database": {
            "sync": db_health,
            "async": async_db,
        },
        "system": sys_info,
    }


@router.get("/health/ready", summary="Readiness probe")
async def readiness_probe():
    """Kubernetes-style readiness probe."""
    db_health = await check_db_health()
    if not db_health:
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail="Database not ready")
    return {"status": "ready"}


@router.get("/health/live", summary="Liveness probe")
async def liveness_probe():
    """Kubernetes-style liveness probe."""
    return {"status": "alive"}
