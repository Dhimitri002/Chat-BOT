"""Auth Router - Endpoints de autenticação."""
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_db
from backend.config import settings
from backend.models.user import User
from backend.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
)
from backend.services.auth_service import (
    create_access_token,
    create_token_pair,
    hash_password,
    verify_password,
)

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Login com email e senha. Retorna JWT token."""
    # Buscar usuário pelo email
    result = await db.execute(select(User).where(User.email == request.email))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos",
        )

    if not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Conta desativada. Contate o suporte.",
        )

    # Atualizar último login
    user.last_login = datetime.utcnow()
    await db.commit()

    # Gerar tokens
    tokens = create_token_pair(
        user_id=str(user.id),
        email=user.email,
        role=user.role,
    )

    return TokenResponse(
        access_token=tokens["access_token"],
        token_type="bearer",
        expires_in=tokens["expires_in"],
    )


@router.post("/register", response_model=TokenResponse)
async def register(request: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Registrar novo usuário. Retorna JWT token."""
    # Verificar se email já existe
    result = await db.execute(select(User).where(User.email == request.email))
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email já cadastrado",
        )

    # Criar novo usuário
    new_user = User(
        email=request.email,
        hashed_password=hash_password(request.password),
        full_name=request.full_name,
        role="user",
        is_active=True,
        is_verified=False,
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    # Gerar tokens
    tokens = create_token_pair(
        user_id=str(new_user.id),
        email=new_user.email,
        role=new_user.role,
    )

    return TokenResponse(
        access_token=tokens["access_token"],
        token_type="bearer",
        expires_in=tokens["expires_in"],
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(refresh_token: str, db: AsyncSession = Depends(get_db)):
    """Renova access token usando refresh token."""
    from backend.services.auth_service import decode_token

    token_data = decode_token(refresh_token)
    if not token_data or not token_data.user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
        )

    # Verificar se usuário ainda existe e está ativo
    result = await db.execute(select(User).where(User.id == token_data.user_id))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado ou desativado",
        )

    # Gerar novo par de tokens
    tokens = create_token_pair(
        user_id=str(user.id),
        email=user.email,
        role=user.role,
    )

    return TokenResponse(
        access_token=tokens["access_token"],
        token_type="bearer",
        expires_in=tokens["expires_in"],
    )


from datetime import datetime  # noqa: E402
