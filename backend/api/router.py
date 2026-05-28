"""
API Router v1 — registro central de todos os endpoints.
"""
from fastapi import APIRouter

from backend.api.v1 import (
    admin,
    analytics,
    auth,
    billing,
    bots,
    chat,
    commands,
    flora,
    health,
    intents,
    licenses,
    notifications,
    plans,
    users,
    whatsapp,
    webhooks,
)

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(bots.router)
api_router.include_router(licenses.router)
api_router.include_router(plans.router)
api_router.include_router(chat.router)
api_router.include_router(commands.router)
api_router.include_router(whatsapp.router)
api_router.include_router(flora.router)
api_router.include_router(admin.router)
api_router.include_router(webhooks.router)
api_router.include_router(intents.router)
api_router.include_router(billing.router)
api_router.include_router(notifications.router)
api_router.include_router(analytics.router)
api_router.include_router(health.router)
