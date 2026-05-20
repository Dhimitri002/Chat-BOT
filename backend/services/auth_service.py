"""Auth Service"""
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger

from backend.models.user import User
from backend.core.security import hash_password, verify_password, create_access_token, create_refresh_token
from backend.schemas.auth import RegisterRequest, LoginRequest


async def register_user(db: AsyncSession, data: RegisterRequest) -> User:
    # Check if email exists
    result = await db.execute(select(User).where(User.email == data.email))
    if result.scalar_one_or_none():
        raise ValueError("Email already registered")

    user = User(
        email=data.email,
        password_hash=hash_password(data.password),
        full_name=data.full_name,
        role="client",
    )
    db.add(user)
    await db.flush()
    logger.info(f"User registered: {user.email}")
    return user


async def authenticate_user(db: AsyncSession, data: LoginRequest) -> dict:
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(data.password, user.password_hash):
        if user:
            user.login_attempts += 1
            if user.login_attempts >= 5:
                user.locked_until = datetime.now(timezone.utc) + __import__("datetime").timedelta(minutes=30)
        raise ValueError("Invalid email or password")

    if user.locked_until and user.locked_until > datetime.now(timezone.utc):
        raise ValueError("Account is locked. Try again later.")

    if not user.is_active:
        raise ValueError("Account is deactivated")

    # Reset attempts on success
    user.login_attempts = 0
    user.last_login_at = datetime.now(timezone.utc)

    access_token = create_access_token(user.id, user.role)
    refresh_token = create_refresh_token(user.id)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": 900,
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "is_active": user.is_active,
            "is_2fa_enabled": user.is_2fa_enabled,
            "created_at": user.created_at.isoformat(),
        },
    }
