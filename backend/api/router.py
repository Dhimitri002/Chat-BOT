"""API Router — Agregador de todas as rotas da API."""
from fastapi import APIRouter

from backend.api.v1 import admin, analytics, auth, billing, bots, chat, commands
from backend.api.v1 import flora, health, intents, licenses, notifications, plans
from backend.api.v1 import users, webhooks, whatsapp

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(bots.router, prefix="/bots", tags=["Bots"])
api_router.include_router(chat.router, prefix="/chat", tags=["Chat"])
api_router.include_router(commands.router, prefix="/commands", tags=["Commands"])
api_router.include_router(flora.router, prefix="/flora", tags=["Flora AI"])
api_router.include_router(intents.router, prefix="/intents", tags=["Intents"])
api_router.include_router(whatsapp.router, prefix="/whatsapp", tags=["WhatsApp"])
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["Webhooks"])
api_router.include_router(billing.router, prefix="/billing", tags=["Billing"])
api_router.include_router(plans.router, prefix="/plans", tags=["Plans"])
api_router.include_router(licenses.router, prefix="/licenses", tags=["Licenses"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
api_router.include_router(admin.router, prefix="/admin", tags=["Admin"])
