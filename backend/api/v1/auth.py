"""Auth Endpoints"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, RefreshRequest
from backend.services.auth_service import register_user, authenticate_user
from backend.api.deps import get_current_user
from backend.models.user import User

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=dict)
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    try:
        user = await register_user(db, data)
        return {"success": True, "user_id": user.id, "message": "Registrado com sucesso!"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=dict)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    try:
        return await authenticate_user(db, data)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/refresh", response_model=dict)
async def refresh(data: RefreshRequest):
    from backend.core.security import decode_token, create_access_token, create_refresh_token
    payload = decode_token(data.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user_id = payload["sub"]
    new_access = create_access_token(user_id, payload.get("role", "client"))
    new_refresh = create_refresh_token(user_id)
    return {
        "access_token": new_access,
        "refresh_token": new_refresh,
        "token_type": "bearer",
        "expires_in": 900,
    }


@router.get("/me", response_model=dict)
async def me(user: User = Depends(get_current_user)):
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "is_active": user.is_active,
        "is_2fa_enabled": user.is_2fa_enabled,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }
