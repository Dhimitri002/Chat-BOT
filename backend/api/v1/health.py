"""Health Check Endpoint - Verificação de saúde do sistema."""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_db
from backend.config import settings

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Health check completo do sistema.
    Verifica: banco de dados, Redis, WhatsApp Manager, LLM Router.
    """
    health = {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "checks": {},
    }

    # Check Database
    try:
        await db.execute(text("SELECT 1"))
        health["checks"]["database"] = {"status": "ok", "latency_ms": 0}
    except Exception as e:
        health["checks"]["database"] = {"status": "error", "error": str(e)}
        health["status"] = "degraded"

    # Check WhatsApp Manager
    try:
        from backend.core.whatsapp_manager import whatsapp_manager
        active_sessions = len(whatsapp_manager.sessions)
        health["checks"]["whatsapp_manager"] = {
            "status": "ok",
            "active_sessions": active_sessions,
        }
    except Exception as e:
        health["checks"]["whatsapp_manager"] = {"status": "error", "error": str(e)}

    # Check LLM Router
    try:
        from backend.core.llm_router import llm_router
        available_models = llm_router.get_available_models()
        health["checks"]["llm_router"] = {
            "status": "ok",
            "available_models": len(available_models),
        }
    except Exception as e:
        health["checks"]["llm_router"] = {"status": "error", "error": str(e)}

    # Check Redis (if configured)
    if settings.REDIS_URL:
        try:
            import aioredis
            redis = aioredis.from_url(settings.REDIS_URL)
            await redis.ping()
            await redis.close()
            health["checks"]["redis"] = {"status": "ok"}
        except Exception as e:
            health["checks"]["redis"] = {"status": "error", "error": str(e)}
    else:
        health["checks"]["redis"] = {"status": "not_configured"}

    return health


@router.get("/health/simple")
async def simple_health():
    """Health check simples (sem verificar dependências)."""
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": settings.APP_VERSION,
    }


@router.get("/health/ready")
async def readiness_check(db: AsyncSession = Depends(get_db)):
    """Readiness check para Kubernetes/Docker."""
    try:
        await db.execute(text("SELECT 1"))
        return {"ready": True}
    except Exception:
        return {"ready": False}


@router.get("/health/live")
async def liveness_check():
    """Liveness check para Kubernetes/Docker."""
    return {"alive": True}
