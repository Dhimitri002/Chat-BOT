"""
Flora Platform — Authentication Service
=========================================
Handles user authentication, registration, token management,
account lockout, session management, and audit logging.
"""
from __future__ import annotations

import logging
import secrets
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.core.security import (
    TokenBlacklistedError,
    TokenExpiredError,
    TokenInvalidError,
    create_access_token,
    create_refresh_token,
    create_token_pair,
    decode_token,
    get_password_hash,
    revoke_token,
    validate_password_strength,
    verify_password,
)
from backend.models.audit_log import AuditAction, AuditLog, AuditSeverity
from backend.models.user import User

logger = logging.getLogger(__name__)


# ─── Account Lockout Tracker ──────────────────────────────

@dataclass
class _LockoutEntry:
    """Track failed login attempts for a user."""
    failed_count: int = 0
    first_attempt: float = 0.0
    locked_until: Optional[float] = None


class AccountLockoutManager:
    """
    Manages account lockout after N failed login attempts.

    Config:
        - max_attempts: Number of failed attempts before lockout
        - lockout_window: Time window for counting attempts (seconds)
        - lockout_duration: How long the account stays locked (seconds)
    """

    def __init__(
        self,
        max_attempts: int = 5,
        lockout_window: int = 900,
        lockout_duration: int = 1800,
    ):
        self._max_attempts = max_attempts
        self._lockout_window = lockout_window
        self._lockout_duration = lockout_duration
        self._entries: dict[str, _LockoutEntry] = defaultdict(_Lockout_entry)

    def is_locked(self, identifier: str) -> bool:
        """Check if an account is currently locked."""
        entry = self._entries.get(identifier)
        if entry is None or entry.locked_until is None:
            return False
        if time.monotonic() > entry.locked_until:
            # Lockout expired, reset
            entry.locked_until = None
            entry.failed_count = 0
            return False
        return True

    def record_failure(self, identifier: str) -> None:
        """Record a failed login attempt."""
        now = time.monotonic()
        entry = self._entries[identifier]

        # Reset if outside the window
        if now - entry.first_attempt > self._lockout_window:
            entry.failed_count = 0
            entry.first_attempt = now
            entry.locked_until = None

        if entry.failed_count == 0:
            entry.first_attempt = now

        entry.failed_count += 1

        if entry.failed_count >= self._max_attempts:
            entry.locked_until = now + self._lockout_duration
            logger.warning(
                "ACCOUNT_LOCKED identifier=%s attempts=%d locked_until=%.0f",
                identifier,
                entry.failed_count,
                entry.locked_until,
            )

    def record_success(self, identifier: str) -> None:
        """Reset lockout tracking on successful login."""
        if identifier in self._entries:
            del self._entries[identifier]

    def get_remaining_attempts(self, identifier: str) -> int:
        """Get remaining attempts before lockout."""
        entry = self._entries.get(identifier)
        if entry is None:
            return self._max_attempts
        return max(0, self._max_attempts - entry.failed_count)

    def get_lockout_remaining_seconds(self, identifier: str) -> int:
        """Get remaining lockout time in seconds."""
        entry = self._entries.get(identifier)
        if entry is None or entry.locked_until is None:
            return 0
        remaining = int(entry.locked_until - time.monotonic())
        return max(0, remaining)


# Global lockout manager
_lockout_manager = AccountLockoutManager(
    max_attempts=settings.RATE_LIMIT_LOGIN_MAX,
    lockout_window=settings.RATE_LIMIT_LOGIN_WINDOW,
    lockout_duration=1800,  # 30 minutes
)


# ─── Custom Exceptions ────────────────────────────────────


class AuthError(Exception):
    """Base authentication error."""
    def __init__(self, message: str, code: str = "AUTH_ERROR"):
        self.message = message
        self.code = code
        super().__init__(message)


class InvalidCredentialsError(AuthError):
    """Invalid email or password."""
    def __init__(self):
        super().__init__("Credenciais invalidas", "INVALID_CREDENTIALS")


class AccountLockedError(AuthError):
    """Account is temporarily locked."""
    def __init__(self, retry_after: int = 0):
        self.retry_after = retry_after
        super().__init__(
            f"Conta bloqueada temporariamente. Tente novamente em {retry_after}s.",
            "ACCOUNT_LOCKED",
        )


class UserAlreadyExistsError(AuthError):
    """User with this email already exists."""
    def __init__(self):
        super().__init__("Usuario ja existe com este email", "USER_EXISTS")


class UserNotFoundError(AuthError):
    """User not found."""
    def __init__(self):
        super().__init__("Usuario nao encontrado", "USER_NOT_FOUND")


class WeakPasswordError(AuthError):
    """Password does not meet strength requirements."""
    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("Senha nao atende os requisitos de seguranca", "WEAK_PASSWORD")


# ─── Auth Service ─────────────────────────────────────────


class AuthService:
    """Authentication service for Flora Platform."""

    def __init__(self, db: AsyncSession):
        self._db = db

    # ─── Registration ──────────────────────────────────────────

    async def register(
        self,
        email: str,
        password: str,
        full_name: str,
        phone: Optional[str] = None,
    ) -> User:
        """
        Register a new user.

        Args:
            email: User email (unique)
            password: Plain text password (will be hashed)
            full_name: User's full name
            phone: Optional phone number

        Returns:
            Created User object

        Raises:
            UserAlreadyExistsError: If email is already registered
            WeakPasswordError: If password doesn't meet requirements
        """
        # Validate password strength
        is_valid, errors = validate_password_strength(password)
        if not is_valid:
            raise WeakPasswordError(errors)

        # Check if user already exists
        existing = await self._db.execute(
            select(User).where(User.email == email.lower().strip())
        )
        if existing.scalar_one_or_none():
            raise UserAlreadyExistsError()

        # Create user
        user = User(
            email=email.lower().strip(),
            hashed_password=get_password_hash(password),
            full_name=full_name.strip(),
            phone=phone.strip() if phone else None,
            role="user",
            is_active=True,
        )
        self._db.add(user)
        await self._db.flush()

        # Audit log
        await self._log_audit(
            action=AuditAction.USER_REGISTERED,
            severity=AuditSeverity.INFO,
            user_id=str(user.id),
            description=f"Usuario registrado: {email}",
        )

        logger.info("USER_REGISTERED id=%s email=%s", user.id, email)
        return user

    # ─── Login ──────────────────────────────────────────────────

    async def login(
        self,
        email: str,
        password: str,
        ip_address: Optional[str] = None,
    ) -> dict:
        """
        Authenticate a user and return tokens.

        Args:
            email: User email
            password: Plain text password
            ip_address: Client IP for audit logging

        Returns:
            Dict with access_token, refresh_token, token_type, expires_in

        Raises:
            AccountLockedError: If account is locked
            InvalidCredentialsError: If credentials are wrong
        """
        normalized_email = email.lower().strip()

        # Check lockout
        if _lockout_manager.is_locked(normalized_email):
            remaining = _lockout_manager.get_lockout_remaining_seconds(normalized_email)
            await self._log_audit(
                action=AuditAction.ACCOUNT_LOCKED,
                severity=AuditSeverity.WARNING,
                description=f"Tentativa de login em conta bloqueada: {normalized_email}",
                ip_address=ip_address,
            )
            raise AccountLockedError(retry_after=remaining)

        # Find user
        result = await self._db.execute(
            select(User).where(User.email == normalized_email)
        )
        user = result.scalar_one_or_none()

        if user is None:
            # Record failure even for non-existent users (timing attack prevention)
            _lockout_manager.record_failure(normalized_email)
            raise InvalidCredentialsError()

        # Verify password
        if not verify_password(password, user.hashed_password):
            _lockout_manager.record_failure(normalized_email)
            remaining = _lockout_manager.get_remaining_attempts(normalized_email)

            await self._log_audit(
                action=AuditAction.LOGIN_FAILED,
                severity=AuditSeverity.WARNING,
                user_id=str(user.id),
                description=f"Falha de login para {normalized_email}. Tentativas restantes: {remaining}",
                ip_address=ip_address,
            )
            raise InvalidCredentialsError()

        # Check if user is active
        if not user.is_active:
            await self._log_audit(
                action=AuditAction.LOGIN_FAILED,
                severity=AuditSeverity.WARNING,
                user_id=str(user.id),
                description=f"Tentativa de login em conta inativa: {normalized_email}",
                ip_address=ip_address,
            )
            raise AuthError("Conta desativada", "ACCOUNT_INACTIVE")

        # Success — reset lockout
        _lockout_manager.record_success(normalized_email)

        # Update last login
        user.last_login = datetime.now(timezone.utc)
        await self._db.flush()

        # Generate tokens
        tokens = create_token_pair(str(user.id), role=user.role)

        await self._log_audit(
            action=AuditAction.LOGIN_SUCCESS,
            severity=AuditSeverity.INFO,
            user_id=str(user.id),
            description=f"Login bem-sucedido: {normalized_email}",
            ip_address=ip_address,
        )

        logger.info("LOGIN_SUCCESS id=%s email=%s", user.id, normalized_email)
        return tokens

    # ─── Token Refresh ─────────────────────────────────────────

    async def refresh_tokens(self, refresh_token: str) -> dict:
        """
        Refresh an access token using a refresh token.

        Args:
            refresh_token: Valid refresh token

        Returns:
            New token pair dict

        Raises:
            AuthError: If refresh token is invalid
        """
        try:
            payload = decode_token(refresh_token)
        except TokenExpiredError:
            raise AuthError("Refresh token expirado", "TOKEN_EXPIRED")
        except TokenBlacklistedError:
            raise AuthError("Refresh token foi revogado", "TOKEN_REVOKED")
        except TokenInvalidError as e:
            raise AuthError(f"Token invalido: {e}", "TOKEN_INVALID")

        if payload.get("type") != "refresh":
            raise AuthError("Token nao e um refresh token", "INVALID_TOKEN_TYPE")

        user_id = payload.get("sub")
        if not user_id:
            raise AuthError("Token sem identificador de usuario", "INVALID_TOKEN")

        # Verify user still exists and is active
        result = await self._db.execute(
            select(User).where(User.id == int(user_id))
        )
        user = result.scalar_one_or_none()

        if user is None:
            raise AuthError("Usuario nao encontrado", "USER_NOT_FOUND")

        if not user.is_active:
            raise AuthError("Conta desativada", "ACCOUNT_INACTIVE")

        # Revoke old refresh token (rotation)
        revoke_token(refresh_token)

        # Issue new token pair
        return create_token_pair(user_id, role=user.role)

    # ─── Logout ─────────────────────────────────────────────────

    async def logout(self, access_token: str, refresh_token: Optional[str] = None) -> None:
        """
        Logout a user by blacklisting their tokens.

        Args:
            access_token: Current access token
            refresh_token: Optional refresh token to also revoke
        """
        try:
            payload = decode_token(access_token)
            user_id = payload.get("sub")
        except (TokenExpiredError, TokenInvalidError, TokenBlacklistedError):
            # Even if expired, try to revoke
            try:
                from jose import jwt as jose_jwt
                payload = jose_jwt.decode(
                    access_token,
                    settings.SECRET_KEY,
                    algorithms=[settings.JWT_ALGORITHM],
                    options={"verify_exp": False},
                )
                user_id = payload.get("sub")
            except Exception:
                return

        # Revoke access token
        revoke_token(access_token)

        # Revoke refresh token if provided
        if refresh_token:
            revoke_token(refresh_token)

        if user_id:
            await self._log_audit(
                action=AuditAction.LOGOUT,
                severity=AuditSeverity.INFO,
                user_id=user_id,
                description="Logout realizado",
            )
            logger.info("LOGOUT user_id=%s", user_id)

    # ─── Get Current User ──────────────────────────────────────

    async def get_current_user(self, user_id: str) -> User:
        """
        Get the current user by ID.

        Raises:
            UserNotFoundError: If user doesn't exist
        """
        result = await self._db.execute(
            select(User).where(User.id == int(user_id))
        )
        user = result.scalar_one_or_none()

        if user is None:
            raise UserNotFoundError()

        return user

    # ─── Change Password ───────────────────────────────────────

    async def change_password(
        self,
        user_id: str,
        current_password: str,
        new_password: str,
    ) -> None:
        """
        Change a user's password.

        Args:
            user_id: User ID
            current_password: Current plain text password
            new_password: New plain text password

        Raises:
            UserNotFoundError: If user doesn't exist
            InvalidCredentialsError: If current password is wrong
            WeakPasswordError: If new password doesn't meet requirements
        """
        result = await self._db.execute(
            select(User).where(User.id == int(user_id))
        )
        user = result.scalar_one_or_none()

        if user is None:
            raise UserNotFoundError()

        # Verify current password
        if not verify_password(current_password, user.hashed_password):
            raise InvalidCredentialsError()

        # Validate new password strength
        is_valid, errors = validate_password_strength(new_password)
        if not is_valid:
            raise WeakPasswordError(errors)

        # Update password
        user.hashed_password = get_password_hash(new_password)
        await self._db.flush()

        await self._log_audit(
            action=AuditAction.PASSWORD_CHANGED,
            severity=AuditSeverity.INFO,
            user_id=user_id,
            description="Senha alterada com sucesso",
        )
        logger.info("PASSWORD_CHANGED user_id=%s", user_id)

    # ─── Forgot Password (Placeholder) ─────────────────────────

    async def forgot_password(self, email: str) -> None:
        """
        Initiate password reset flow.

        Always returns success to prevent email enumeration.
        In production, sends a reset email with a secure token.
        """
        normalized_email = email.lower().strip()
        result = await self._db.execute(
            select(User).where(User.email == normalized_email)
        )
        user = result.scalar_one_or_none()

        if user is not None:
            # Generate reset token
            reset_token = create_access_token(
                str(user.id),
                role=user.role,
                expires_delta=__import__("datetime").timedelta(hours=1),
                extra_claims={"type": "password_reset"},
            )

            await self._log_audit(
                action=AuditAction.PASSWORD_RESET_REQUESTED,
                severity=AuditSeverity.INFO,
                user_id=str(user.id),
                description=f"Solicitacao de redefinicao de senha: {normalized_email}",
            )
            logger.info("PASSWORD_RESET_REQUESTED user_id=%s email=%s", user.id, normalized_email)

            # In production: send email with reset_token link
            # await email_service.send_reset_email(user.email, reset_token)

        # Always log the attempt (don't reveal if email exists)
        logger.info("FORGOT_PASSWORD_REQUESTED email=%s", normalized_email)

    # ─── Audit Logging ─────────────────────────────────────────

    async def _log_audit(
        self,
        action: AuditAction,
        severity: AuditSeverity,
        user_id: Optional[str] = None,
        description: str = "",
        ip_address: Optional[str] = None,
        metadata_: Optional[dict] = None,
    ) -> None:
        """Create an audit log entry."""
        try:
            log_entry = AuditLog(
                user_id=int(user_id) if user_id else None,
                action=action,
                severity=severity,
                description=description,
                ip_address=ip_address,
                metadata_=metadata_ or {},
            )
            self._db.add(log_entry)
            await self._db.flush()
        except Exception as e:
            logger.error("AUDIT_LOG_ERROR: %s", e)
