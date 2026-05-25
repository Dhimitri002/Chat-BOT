"""
API Router v1 — registro central de todos os endpoints.
"""
from fastapi import APIRouter

from backend.api.v1 import (
    admin,
    auth,
    bots,
    chat,
    commands,
    flora,
    health,
    licenses,
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
