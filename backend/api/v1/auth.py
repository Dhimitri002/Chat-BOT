"""Flora Platform — Authentication Endpoints"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user, get_db
from backend.models.user import User
from backend.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RefreshRequest,
    RegisterRequest,
    UserResponse,
)
from backend.services.auth_service import (
    AccountLockedError,
    AuthService,
    InvalidCredentialsError,
    UserAlreadyExistsError,
)
from backend.core.security import create_access_token, create_refresh_token
from backend.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Register a new user account."""
    try:
        svc = AuthService(db)
        user = await svc.register(
            email=body.email,
            password=body.password,
            full_name=body.name or body.email.split("@")[0],
        )
        await db.commit()
        return UserResponse(
            id=str(user.id),
            email=user.email,
            name=user.full_name,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at.isoformat() if user.created_at else None,
        )
    except UserAlreadyExistsError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email já registrado")
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        await db.rollback()
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao registrar usuário",
        )


@router.post("/login", response_model=LoginResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate and receive access + refresh tokens."""
    svc = AuthService(db)
    try:
        tokens = await svc.login(email=body.email, password=body.password)
        return LoginResponse(
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            token_type=tokens.get("token_type", "bearer"),
            expires_in=tokens.get("expires_in", 1800),
        )
    except AccountLockedError as e:
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=f"Conta bloqueada. Tente novamente em {e.retry_after}s",
            headers={"Retry-After": str(e.retry_after)},
        )
    except InvalidCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha inválidos",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/refresh", response_model=LoginResponse)
async def refresh_token(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """Refresh an access token using a valid refresh token."""
    svc = AuthService(db)
    try:
        tokens = await svc.refresh_tokens(body.refresh_token)
        return LoginResponse(
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            token_type=tokens.get("token_type", "bearer"),
            expires_in=tokens.get("expires_in", 1800),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token inválido ou expirado: {e}",
        )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current authenticated user profile."""
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        name=current_user.full_name,
        role=current_user.role,
        is_active=current_user.is_active,
        created_at=current_user.created_at.isoformat() if current_user.created_at else None,
    )


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """Logout current user (client should discard tokens)."""
    return {"success": True, "message": "Logout realizado com sucesso"}
