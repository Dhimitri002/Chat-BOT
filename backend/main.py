"""Flora Platform — FastAPI Backend"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from backend.config import get_settings
from backend.database import init_db
from backend.api.router import api_router
from backend.scripts.seed_plans import seed_plans

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"🌸 {settings.APP_NAME} v{settings.APP_VERSION} starting...")
    await init_db()
    logger.info("Database initialized")
    yield
    logger.info("🌸 Flora Platform shutting down...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Plataforma de chatbots licenciados para WhatsApp",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health")
async def health():
    return {"status": "healthy", "app": settings.APP_NAME, "version": settings.APP_VERSION}
