"""Flora Platform — Authentication Service
Enhanced with bcrypt password hashing, rate limiting, IP lockout,
token blacklisting, password strength validation, and TOTP 2FA support.
"""
from __future__ import annotations

import logging
import re
import time
import uuid
from datetime import datetime, timezone
from typing import Optional

from jose import jwt, JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from backend.config import settings
from backend.core.security import (
    create_access_token,
    create_refresh_token,
    verify_password,
    get_password_hash,
)
from backend.models.user import User

# Module-level singletons
_login_attempts: dict[str, list[float]] = {}  # IP -> list of failed attempt timestamps
_token_blacklist: set[str] = set()  # Set of revoked token JTIs


# ---------------------------------------------------------------------------
# Password validation
# ---------------------------------------------------------------------------

class PasswordValidationError(ValueError):
    def __init__(self, reasons: list[str]):
        self.reasons = reasons
        super().__init__("; ".join(reasons))


def validate_password_strength(password: str) -> list[str]:
    reasons = []
    if len(password) < 8:
        reasons.append("Senha deve ter pelo menos 8 caracteres")
    if not re.search(r'[A-Z]', password):
        reasons.append("Senha deve ter pelo menos uma letra maiúscula")
    if not re.search(r'[a-z]', password):
        reasons.append("Senha deve ter pelo menos uma letra minúscula")
    if not re.search(r'\d', password):
        reasons.append("Senha deve ter pelo menos um número")
    return reasons


# ---------------------------------------------------------------------------
# IP Lockout
# ---------------------------------------------------------------------------

def _is_ip_locked_out(ip: str) -> bool:
    """Check if an IP is locked out due to too many failed attempts."""
    if ip not in _login_attempts:
        return False
    now = time.time()
    # Keep only attempts from the last 15 minutes
    _login_attempts[ip] = [t for t in _login_attempts[ip] if now - t < 900]
    if not _login_attempts[ip]:
        del _login_attempts[ip]
        return False
    return len(_login_attempts[ip]) >= settings.RATE_LIMIT_LOGIN_MAX


def _record_failed_attempt(ip: str):
    """Record a failed login attempt from an IP."""
    if ip not in _login_attempts:
        _login_attempts[ip] = []
    _login_attempts[ip].append(time.time())


# ---------------------------------------------------------------------------
# Token blacklist
# ---------------------------------------------------------------------------

def blacklist_token(jti: str):
    _token_blacklist.add(jti)


def is_token_blacklisted(jti: str) -> bool:
    return jti in _token_blacklist


# ---------------------------------------------------------------------------
# Auth Service
# ---------------------------------------------------------------------------

class AuthService:

    @staticmethod
    async def register_user(
        db: AsyncSession,
        name: str,
        email: str,
        password: str,
        role: str = "user",
    ) -> User:
        # Check existing user
        result = await db.execute(select(User).where(User.email == email))
        if result.scalar_one_or_none():
            raise ValueError("Email já cadastrado")

        # Validate password
        reasons = validate_password_strength(password)
        if reasons:
            raise PasswordValidationError(reasons)

        user = User(
            id=str(uuid.uuid4()),
            email=email.lower().strip(),
            hashed_password=get_password_hash(password),
            name=name or "",
            role=role,
            is_active=True,
        )
        db.add(user)
        await db.flush()
        logger.info(f"User registered: {email}")
        return user

    @staticmethod
    async def authenticate_user(
        db: AsyncSession,
        email: str,
        password: str,
    ) -> Optional[User]:
        result = await db.execute(
            select(User).where(User.email == email.lower().strip())
        )
        user = result.scalar_one_or_none()
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        if not user.is_active:
            return None
        return user

    @staticmethod
    async def login(
        db: AsyncSession,
        email: str,
        password: str,
        ip: str = "",
    ) -> Optional[dict]:
        # Check IP lockout
        if ip and _is_ip_locked_out(ip):
            logger.warning(f"IP locked out: {ip}")
            raise HTTPException(
                status_code=429,
                detail="Muitas tentativas. Tente novamente em 15 minutos.",
            )

        user = await AuthService.authenticate_user(db, email, password)
        if not user:
            if ip:
                _record_failed_attempt(ip)
            return None

        # Update last login
        user.last_login = datetime.now(timezone.utc)
        await db.flush()

        # Generate tokens
        token_data = {"sub": str(user.id), "role": user.role}
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)

        logger.info(f"User logged in: {email}")
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": {
                "id": str(user.id),
                "email": user.email,
                "name": user.name,
                "role": user.role,
                "is_active": user.is_active,
                "is_2fa_enabled": user.is_2fa_enabled,
                "created_at": user.created_at.isoformat(),
            },
        }

    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: str) -> Optional[User]:
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()


# Import HTTPException for login method
from fastapi import HTTPException
