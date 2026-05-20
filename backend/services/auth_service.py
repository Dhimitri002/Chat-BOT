"""
Flora Platform — Auth Service
"""
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger

from backend.models.user import User, UserRole
from backend.core.security import hash_password, verify_password, create_access_token, create_refresh_token


async def register_user(db: AsyncSession, email: str, password: str, full_name: str = "", role: str = "user") -> User:
    """Register a new user."""
    existing = (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()
    if existing:
        raise ValueError("Email already registered")

    user = User(
        email=email,
        hashed_password=hash_password(password),
        full_name=full_name,
        role=UserRole(role) if role in [r.value for r in UserRole] else UserRole.USER,
    )
    db.add(user)
    await db.flush()
    logger.info(f"User registered: {user.email}")
    return user


async def authenticate_user(db: AsyncSession, email: str, password: str) -> dict:
    """Authenticate user and return tokens."""
    user = (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()

    if not user or not verify_password(password, user.hashed_password):
        raise ValueError("Invalid email or password")

    if not user.is_active:
        raise ValueError("Account is deactivated")

    user.last_login = datetime.now(timezone.utc)

    access_token = create_access_token(user.id, user.role.value)
    refresh_token = create_refresh_token(user.id)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": 1800,
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role.value,
        },
    }
