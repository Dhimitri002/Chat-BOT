"""Flora Platform — Backend Main (FastAPI)"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from backend.api.router import api_router
from backend.api.middleware.audit import AuditMiddleware
from backend.api.middleware.error_handler import ErrorHandlerMiddleware
from backend.api.middleware.rate_limit import RateLimitMiddleware
from backend.config import settings
from backend.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup e shutdown da aplicação."""
    # Startup
    await init_db()
    print(f"🌸 Flora Platform iniciada — {settings.HOST}:{settings.PORT}")
    yield
    # Shutdown
    print("🌸 Flora Platform encerrada")


def create_app() -> FastAPI:
    """Factory function para criar a aplicação FastAPI."""
    app = FastAPI(
        title="Flora Platform",
        description="Plataforma de Chatbots Licenciados com IA",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # ── CORS ───────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Session ────────────────────────────────────────────
    app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

    # ── Rate Limiting ──────────────────────────────────────
    app.add_middleware(
        RateLimitMiddleware,
        max_requests=settings.RATE_LIMIT_REQUESTS,
        window_seconds=settings.RATE_LIMIT_WINDOW,
    )

    # ── Audit ──────────────────────────────────────────────
    app.add_middleware(AuditMiddleware)

    # ── Error Handler ──────────────────────────────────────
    app.add_middleware(ErrorHandlerMiddleware)

    # ── API Routes ─────────────────────────────────────────
    app.include_router(api_router, prefix="/api/v1")

    # ── Root ───────────────────────────────────────────────
    @app.get("/", include_in_schema=False)
    async def root():
        return {"message": "🌸 Flora Platform API", "docs": "/docs", "version": "1.0.0"}

    return app


# Instância da aplicação
app = create_app()
