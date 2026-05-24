"""FastAPI Dependencies - Injeção de dependências."""
from typing import AsyncGenerator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.license_manager import LicenseManager
from backend.core.security import SecurityManager
from backend.database import async_session
from backend.models.user import User
from backend.services.auth_service import decode_token

security_scheme = HTTPBearer()


async def get_db() -> AsyncGenerator:
    """Yield async database session."""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Extrai e valida o usuário atual do token JWT."""
    token = credentials.credentials
    token_data = decode_token(token)

    if not token_data or not token_data.user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    result = await db.execute(select(User).where(User.id == token_data.user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Conta desativada",
        )

    return user


async def get_current_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """Valida que o usuário atual é admin."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito a administradores",
        )
    return current_user


def get_license_manager() -> LicenseManager:
    """Retorna instância do LicenseManager."""
    return LicenseManager()


def get_security_manager() -> SecurityManager:
    """Retorna instância do SecurityManager."""
    return SecurityManager()
