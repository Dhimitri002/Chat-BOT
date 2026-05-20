"""API Router"""
from fastapi import APIRouter
from backend.api.v1 import auth, licenses, bots

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(licenses.router)
api_router.include_router(bots.router)
