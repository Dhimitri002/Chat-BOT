"""
Flora Platform — Security (Core)
=================================
JWT token creation and verification, password hashing,
and security utilities.

Uses:
- python-jose for JWT (HS256/RS256)
- bcrypt for password hashing
- argon2-cffi as alternative password hasher
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

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


class SecurityManager:
    """
    Central security utility for Flora Platform.

    Handles:
    - JWT token creation and validation
    - Password hashing and verification
    - Token refresh logic
    """

    def __init__(
        self,
        secret_key: Optional[str] = None,
        algorithm: str = "HS256",
        access_token_expire_minutes: int = 30,
        refresh_token_expire_days: int = 7,
    ):
        self._secret_key = secret_key or settings.SECRET_KEY
        self._algorithm = algorithm or settings.JWT_ALGORITHM
        self._access_expire = access_token_expire_minutes
        self._refresh_expire = refresh_token_expire_days

        if not HAS_JOSE:
            raise RuntimeError("python-jose[cryptography] is required for JWT operations")

        if not self._secret_key or len(self._secret_key) < 32:
            logger.warning(
                "SEC_KEY is too short or empty. "
                "Using a generated key — tokens will restart on deploy."
            )
            import secrets
            self._secret_key = secrets.token_hex(32)

    # ─── JWT Tokens ─────────────────────────────────────────────

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
            user_id: The user's unique ID (stored in 'sub' claim)
            role: User role (stored in 'role' claim)
            extra_claims: Additional claims to include
            expires_delta: Custom expiry (default: from config)

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

        Returns the decoded payload.

        Raises:
            TokenExpiredError: If token is expired
            TokenInvalidError: If token is malformed or signature is wrong
        """
        try:
            payload = jose_jwt.decode(
                token,
                self._secret_key,
                algorithms=[self._algorithm],
            )
            return payload
        except jose_jwt.ExpiredSignatureError:
            raise TokenExpiredError("Token expirado")
        except JWTError as e:
            raise TokenInvalidError(f"Token inválido: {e}")

    def refresh_access_token(self, refresh_token: str) -> dict:
        """
        Create a new access token from a refresh token.

        Validates the refresh token first.
        """
        payload = self.decode_token(refresh_token)

        if payload.get("type") != "refresh":
            raise TokenInvalidError("Token não é um refresh token")

        user_id = payload.get("sub")
        if not user_id:
            raise TokenInvalidError("Token sem identificador de usuário")

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
        Hash a password using bcrypt.

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

    # ─── Utilities ───────────────────────────────────────────────

    @staticmethod
    def _generate_jti() -> str:
        """Generate a unique JWT ID."""
        import secrets
        return secrets.token_urlsafe(16)

    @staticmethod
    def generate_api_secret() -> str:
        """Generate a secure API secret."""
        import secrets
        return secrets.token_urlsafe(32)


class TokenError(Exception):
    """Base token error."""
    pass


class TokenExpiredError(TokenError):
    """Token has expired."""
    pass


class TokenInvalidError(TokenError):
    """Token is invalid."""
    pass
