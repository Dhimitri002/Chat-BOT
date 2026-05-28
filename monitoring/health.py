"""
Flora Platform — Server-Side Health Monitor
=============================================

Background monitoring service that periodically checks system health
and logs warnings when thresholds are exceeded.

This is NOT an API module — it runs as a background task.
For API health endpoints, see backend/api/v1/health.py
"""
from __future__ import annotations

import asyncio
import logging
import os
import platform
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

_STARTUP_TIME = time.time()


@dataclass
class HealthSnapshot:
    """Represents a point-in-time health check."""
    timestamp: str = ""
    uptime_seconds: float = 0.0
    cpu_percent: Optional[float] = None
    memory_rss_mb: Optional[float] = None
    memory_percent: Optional[float] = None
    db_connected: bool = False
    status: str = "unknown"
    warnings: list = field(default_factory=list)


def get_uptime_seconds() -> float:
    return round(time.time() - _STARTUP_TIME, 2)


def get_system_snapshot() -> dict:
    """Get current system resource usage."""
    snapshot = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": get_uptime_seconds(),
        "python": platform.python_version(),
        "os": f"{platform.system()} {platform.release()}",
    }
    try:
        import psutil
        process = psutil.Process(os.getpid())
        mem_info = process.memory_info()
        snapshot.update({
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "memory_rss_mb": round(mem_info.rss / (1024 * 1024), 2),
            "memory_vms_mb": round(mem_info.vms / (1024 * 1024), 2),
            "memory_percent": round(process.memory_percent(), 2),
            "system_total_memory_mb": round(psutil.virtual_memory().total / (1024 * 1024), 2),
            "system_available_memory_mb": round(psutil.virtual_memory().available / (1024 * 1024), 2),
            "cpu_count": psutil.cpu_count(),
        })
    except ImportError:
        logger.debug("psutil not available — limited system metrics")
        snapshot["cpu_percent"] = None
        snapshot["memory_rss_mb"] = None
    return snapshot


def check_thresholds(snapshot: dict) -> list[str]:
    """Check system metrics against warning thresholds."""
    warnings = []
    mem_pct = snapshot.get("memory_percent")
    if mem_pct is not None and mem_pct > 85:
        warnings.append(f"High memory usage: {mem_pct}%")
    cpu = snapshot.get("cpu_percent")
    if cpu is not None and cpu > 90:
        warnings.append(f"High CPU usage: {cpu}%")
    avail_mem = snapshot.get("system_available_memory_mb")
    if avail_mem is not None and avail_mem < 500:
        warnings.append(f"Low available memory: {avail_mem}MB")
    return warnings


async def monitor_loop(interval_seconds: int = 60):
    """Background monitoring loop. Call from startup event."""
    logger.info(f"🔍 Health monitor started (interval: {interval_seconds}s)")
    while True:
        try:
            snapshot = get_system_snapshot()
            warnings = check_thresholds(snapshot)
            if warnings:
                for w in warnings:
                    logger.warning(f"⚠️ {w}")
                logger.warning(f"System snapshot: {snapshot}")
            else:
                logger.debug(f"✅ Health OK — CPU: {snapshot.get('cpu_percent')}%, "
                           f"Mem: {snapshot.get('memory_rss_mb')}MB")
        except Exception as e:
            logger.error(f"Monitor error: {e}")
        await asyncio.sleep(interval_seconds)
