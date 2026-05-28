"""
Flora Platform — Security (Core)
=================================
JWT token creation and verification, password hashing,
token blacklisting, rate limiting, input sanitization,
and security utilities.

Uses:
- python-jose for JWT (HS256/RS256)
- bcrypt for password hashing (12 rounds)
- argon2-cffi as alternative password hasher
- secrets for secure token generation
"""
from __future__ import annotations

import functools
import html
import logging
import re
import secrets
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Optional

from backend.config import settings

logger = logging.getLogger(__name__)

try:
    from jose import JWTError, jwt as jose_jwt
    HAS_JOSE = True
except ImportError:
    HAS_JOSE = False
    logger.warning("python-jose not installed, JWT functionality unavailable")

try:
    import bcrypt
    HAS_BCRYPT = True
except ImportError:
    HAS_BCRYPT = False
    logger.warning("bcrypt not installed, password hashing unavailable")

try:
    from argon2 import PasswordHasher as Argon2Hasher
    from argon2.exceptions import VerifyMismatchError
    HAS_ARGON2 = True
except ImportError:
    HAS_ARGON2 = False


# ─── Token Blacklist (In-Memory) ──────────────────────────

class TokenBlacklist:
    """
    In-memory token blacklist for logout.

    Stores revoked token JTIs with automatic expiry cleanup.
    For production, replace with Redis backend.
    """

    def __init__(self):
        self._blacklist: dict[str, datetime] = {}

    def add(self, jti: str, expires_at: datetime) -> None:
        """Add a token JTI to the blacklist."""
        self._blacklist[jti] = expires_at
        self._cleanup()

    def is_blacklisted(self, jti: str) -> bool:
        """Check if a token JTI is blacklisted."""
        self._cleanup()
        return jti in self._blacklist

    def _cleanup(self) -> None:
        """Remove expired entries."""
        now = datetime.now(timezone.utc)
        expired = [jti for jti, exp in self._blacklist.items() if exp <= now]
        for jti in expired:
            del self._blacklist[jti]

    def clear(self) -> None:
        """Clear the entire blacklist (testing)."""
        self._blacklist.clear()


# Global blacklist instance
_token_blacklist = TokenBlacklist()


# ─── Security Manager ─────────────────────────────────────


class SecurityManager:
    """Central security manager for Flora Platform."""

    def __init__(self):
        self._secret_key = settings.SECRET_KEY
        self._algorithm = settings.JWT_ALGORITHM
        self._access_expire = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        self._refresh_expire = settings.REFRESH_TOKEN_EXPIRE_DAYS
        self._blacklist_enabled = settings.TOKEN_BLACKLIST_ENABLED

    # ─── JWT Token Creation ─────────────────────────────────────

    def create_access_token(
        self,
        user_id: str,
        role: str = "user",
        extra_claims: Optional[dict] = None,
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        """
        Create a JWT access token.

        Args:
            user_id: Subject identifier
            role: User role (admin, user, etc.)
            extra_claims: Additional JWT claims
            expires_delta: Custom expiry duration

        Returns:
            Encoded JWT string
        """
        if expires_delta is None:
            expires_delta = timedelta(minutes=self._access_expire)

        now = datetime.now(timezone.utc)
        expire = now + expires_delta

        claims = {
            "sub": str(user_id),
            "role": role,
            "type": "access",
            "iat": now,
            "exp": expire,
            "nbf": now,
            "jti": self._generate_jti(),
        }

        if extra_claims:
            claims.update(extra_claims)

        token = jose_jwt.encode(claims, self._secret_key, algorithm=self._algorithm)
        return token

    def create_refresh_token(
        self,
        user_id: str,
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        """Create a JWT refresh token."""
        if expires_delta is None:
            expires_delta = timedelta(days=self._refresh_expire)

        now = datetime.now(timezone.utc)
        expire = now + expires_delta

        claims = {
            "sub": str(user_id),
            "type": "refresh",
            "iat": now,
            "exp": expire,
            "jti": self._generate_jti(),
        }

        return jose_jwt.encode(claims, self._secret_key, algorithm=self._algorithm)

    def create_token_pair(
        self,
        user_id: str,
        role: str = "user",
        extra_claims: Optional[dict] = None,
    ) -> dict:
        """Create both access and refresh tokens."""
        access = self.create_access_token(user_id, role, extra_claims)
        refresh = self.create_refresh_token(user_id)
        return {
            "access_token": access,
            "refresh_token": refresh,
            "token_type": "bearer",
            "expires_in": self._access_expire * 60,
        }

    def decode_token(self, token: str) -> dict:
        """
        Decode and validate a JWT token.

        Also checks the blacklist if enabled.

        Returns the decoded payload.

        Raises:
            TokenBlacklistedError: If token has been revoked
            TokenExpiredError: If token is expired
            TokenInvalidError: If token is malformed or signature is wrong
        """
        try:
            payload = jose_jwt.decode(
                token,
                self._secret_key,
                algorithms=[self._algorithm],
            )
        except jose_jwt.ExpiredSignatureError:
            raise TokenExpiredError("Token expirado")
        except JWTError as e:
            raise TokenInvalidError(f"Token invalido: {e}")

        # Check blacklist
        if self._blacklist_enabled:
            jti = payload.get("jti")
            if jti and _token_blacklist.is_blacklisted(jti):
                raise TokenBlacklistedError("Token foi revogado")

        return payload

    def revoke_token(self, token: str) -> None:
        """
        Revoke a token by adding its JTI to the blacklist.

        Calculates expiry from the token's exp claim so the
        blacklist entry auto-expires.
        """
        try:
            # Decode without verification of expiry — we want to revoke even expired tokens
            payload = jose_jwt.decode(
                token,
                self._secret_key,
                algorithms=[self._algorithm],
                options={"verify_exp": False},
            )
        except JWTError:
            return

        jti = payload.get("jti")
        exp = payload.get("exp")
        if jti and exp:
            expires_at = datetime.fromtimestamp(exp, tz=timezone.utc)
            _token_blacklist.add(jti, expires_at)

    def refresh_access_token(self, refresh_token: str) -> dict:
        """
        Create a new access token from a refresh token.

        Validates the refresh token first.
        """
        payload = self.decode_token(refresh_token)

        if payload.get("type") != "refresh":
            raise TokenInvalidError("Token nao e um refresh token")

        user_id = payload.get("sub")
        if not user_id:
            raise TokenInvalidError("Token sem identificador de usuario")

        return self.create_token_pair(user_id, role=payload.get("role", "user"))

    def verify_token_type(self, token: str, expected_type: str) -> dict:
        """Decode a token and verify its type (access/refresh)."""
        payload = self.decode_token(token)
        if payload.get("type") != expected_type:
            raise TokenInvalidError(
                f"Esperado token '{expected_type}', recebido '{payload.get('type')}'"
            )
        return payload

    # ─── Password Hashing ────────────────────────────────────────

    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a password using bcrypt with 12 rounds.

        Returns the hashed password string.
        """
        if not HAS_BCRYPT:
            raise RuntimeError("bcrypt is required for password hashing")
        if not password or len(password) < 6:
            raise ValueError("Senha deve ter pelo menos 6 caracteres")
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        if not HAS_BCRYPT:
            raise RuntimeError("bcrypt is required for password verification")
        try:
            return bcrypt.checkpw(
                plain_password.encode("utf-8"),
                hashed_password.encode("utf-8"),
            )
        except Exception:
            return False

    @staticmethod
    def hash_password_argon2(password: str) -> str:
        """Hash password using Argon2id (stronger alternative)."""
        if not HAS_ARGON2:
            raise RuntimeError("argon2-cffi is required for Argon2 hashing")
        hasher = Argon2Hasher()
        return hasher.hash(password)

    @staticmethod
    def verify_password_argon2(password: str, hashed: str) -> bool:
        """Verify an Argon2id hashed password."""
        if not HAS_ARGON2:
            raise RuntimeError("argon2-cffi is required for Argon2 verification")
        try:
            hasher = Argon2Hasher()
            return hasher.verify(hashed, password)
        except VerifyMismatchError:
            return False

    # ─── Password Strength Validation ────────────────────────────

    @staticmethod
    def validate_password_strength(password: str) -> tuple[bool, list[str]]:
        """
        Validate password strength.

        Returns:
            (is_valid, list_of_errors)
        """
        errors: list[str] = []
        cfg = settings

        if len(password) < cfg.PASSWORD_MIN_LENGTH:
            errors.append(f"Senha deve ter pelo menos {cfg.PASSWORD_MIN_LENGTH} caracteres")

        if cfg.PASSWORD_REQUIRE_UPPERCASE and not re.search(r"[A-Z]", password):
            errors.append("Senha deve conter pelo menos uma letra maiuscula")

        if cfg.PASSWORD_REQUIRE_LOWERCASE and not re.search(r"[a-z]", password):
            errors.append("Senha deve conter pelo menos uma letra minuscula")

        if cfg.PASSWORD_REQUIRE_DIGITS and not re.search(r"\d", password):
            errors.append("Senha deve conter pelo menos um numero")

        if cfg.PASSWORD_REQUIRE_SPECIAL and not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?]", password):
            errors.append("Senha deve conter pelo menos um caractere especial")

        return (len(errors) == 0, errors)

    # ─── API Key Generation ──────────────────────────────────────

    @staticmethod
    def generate_api_key() -> str:
        """Generate a secure API key using secrets.token_urlsafe."""
        return secrets.token_urlsafe(32)

    @staticmethod
    def generate_api_secret() -> str:
        """Generate a secure API secret."""
        return secrets.token_urlsafe(32)

    # ─── Input Sanitization ──────────────────────────────────────

    @staticmethod
    def sanitize_html(value: str) -> str:
        """
        Sanitize input to prevent XSS attacks.

        Escapes HTML entities and removes script tags.
        """
        if not value:
            return value
        # Remove script tags and their contents
        value = re.sub(r"<script[^>]*>.*?</script>", "", value, flags=re.IGNORECASE | re.DOTALL)
        # Remove event handlers
        value = re.sub(r"on\w+\s*=", "", value, flags=re.IGNORECASE)
        # Escape HTML entities
        value = html.escape(value)
        return value

    @staticmethod
    def sanitize_sql_input(value: str) -> str:
        """
        Basic SQL injection prevention.

        Note: Parameterized queries are the primary defense.
        This is an additional layer for logging/search fields.
        """
        if not value:
            return value
        # Remove common SQL injection patterns
        dangerous = [
            "--", ";--", "/*", "*/", "@@", "@",
            "char(", "nchar(", "varchar(", "nvarchar(",
            "alter ", "begin ", "cast ", "create ", "cursor ",
            "declare ", "delete ", "drop ", "end ", "exec ",
            "execute ", "fetch ", "insert ", "kill ", "open ",
            "select ", "sys ", "table ", "update ",
        ]
        result = value
        for pattern in dangerous:
            result = re.sub(re.escape(pattern), "", result, flags=re.IGNORECASE)
        return result.strip()

    @staticmethod
    def sanitize_input(value: str) -> str:
        """Full input sanitization (XSS + SQL injection prevention)."""
        value = SecurityManager.sanitize_html(value)
        value = SecurityManager.sanitize_sql_input(value)
        return value

    # ─── Utilities ───────────────────────────────────────────────

    @staticmethod
    def _generate_jti() -> str:
        """Generate a unique JWT ID."""
        return secrets.token_urlsafe(16)


# ─── Rate Limiting Decorator ──────────────────────────────

@dataclass
class _RateLimitState:
    """Track rate limit state per key."""
    count: int = 0
    window_start: float = 0.0


def rate_limit(
    max_requests: int = 100,
    window_seconds: int = 60,
    key_func: Optional[Callable] = None,
):
    """
    Rate limiting decorator for endpoint functions.

    Args:
        max_requests: Maximum requests allowed per window
        window_seconds: Time window in seconds
        key_func: Function to extract rate limit key from args.
                  Defaults to using the first string arg or 'default'.

    Usage:
        @rate_limit(max_requests=5, window_seconds=60)
        async def login(request: Request, ...):
            ...
    """
    _states: dict[str, _RateLimitState] = defaultdict(_RateLimitState)

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            if key_func:
                key = key_func(*args, **kwargs)
            else:
                # Default: use first string arg or 'default'
                key = "default"
                for arg in args:
                    if isinstance(arg, str):
                        key = arg
                        break

            now = time.monotonic()
            state = _states[key]

            if now - state.window_start >= window_seconds:
                state.count = 0
                state.window_start = now

            state.count += 1

            if state.count > max_requests:
                from fastapi import HTTPException
                raise HTTPException(
                    status_code=429,
                    detail="Limite de requisicoes excedido. Tente novamente em breve.",
                )

            return await func(*args, **kwargs)

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            if key_func:
                key = key_func(*args, **kwargs)
            else:
                key = "default"
                for arg in args:
                    if isinstance(arg, str):
                        key = arg
                        break

            now = time.monotonic()
            state = _states[key]

            if now - state.window_start >= window_seconds:
                state.count = 0
                state.window_start = now

            state.count += 1

            if state.count > max_requests:
                from fastapi import HTTPException
                raise HTTPException(
                    status_code=429,
                    detail="Limite de requisicoes excedido. Tente novamente em breve.",
                )

            return func(*args, **kwargs)

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


# ─── Custom Exceptions ────────────────────────────────────


class TokenError(Exception):
    """Base token error."""
    pass


class TokenExpiredError(TokenError):
    """Token has expired."""
    pass


class TokenInvalidError(TokenError):
    """Token is invalid."""
    pass


class TokenBlacklistedError(TokenError):
    """Token has been revoked/blacklisted."""
    pass


# ─── Module-Level Convenience Functions ───────────────────
# These are used by auth_service.py and tests as bare imports.

_singleton = SecurityManager()


def create_access_token(user_id: str, role: str = "user", **extra_claims) -> str:
    """Create a JWT access token. Thin wrapper around SecurityManager."""
    return _singleton.create_access_token(user_id, role, extra_claims=extra_claims or None)


def create_refresh_token(user_id: str) -> str:
    """Create a JWT refresh token. Thin wrapper around SecurityManager."""
    return _singleton.create_refresh_token(user_id)


def create_token_pair(user_id: str, role: str = "user", **extra_claims) -> dict:
    """Create access + refresh token pair. Thin wrapper around SecurityManager."""
    return _singleton.create_token_pair(user_id, role, extra_claims=extra_claims or None)


def decode_token(token: str) -> dict:
    """Decode and validate a JWT token. Thin wrapper around SecurityManager."""
    return _singleton.decode_token(token)


def revoke_token(token: str) -> None:
    """Revoke a token (add to blacklist). Thin wrapper around SecurityManager."""
    _singleton.revoke_token(token)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash. Thin wrapper around SecurityManager."""
    return _singleton.verify_password(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt. Thin wrapper around SecurityManager."""
    return _singleton.hash_password(password)


def validate_password_strength(password: str) -> tuple[bool, list[str]]:
    """Validate password strength. Thin wrapper around SecurityManager."""
    return _singleton.validate_password_strength(password)


def generate_api_key() -> str:
    """Generate a secure API key. Thin wrapper around SecurityManager."""
    return _singleton.generate_api_key()


def sanitize_input(value: str) -> str:
    """Sanitize user input. Thin wrapper around SecurityManager."""
    return _singleton.sanitize_input(value)


def is_token_blacklisted(jti: str) -> bool:
    """Check if a token JTI is blacklisted."""
    return _token_blacklist.is_blacklisted(jti)


def get_token_blacklist() -> TokenBlacklist:
    """Get the global token blacklist instance."""
    return _token_blacklist
