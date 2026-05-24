"""Flora Platform — Security Core"""
import hashlib
import hmac
import secrets
import base64
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from backend.config import settings
ph = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=4)


# ─── Password Hashing ───

def hash_password(password: str) -> str:
    return ph.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return ph.verify(password_hash, password)
    except VerifyMismatchError:
        return False


# ─── JWT Tokens ───

def create_access_token(user_id: str, role: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "role": role,
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        "jti": secrets.token_hex(16),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "type": "refresh",
        "iat": now,
        "exp": now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        "jti": secrets.token_hex(16),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


# ─── Encryption (AES-256-GCM) ───

class EncryptionService:
    def __init__(self):
        key_bytes = settings.ENCRYPTION_KEY.encode()
        if len(key_bytes) < 32:
            key_bytes = key_bytes.ljust(32, b"\0")
        self.aesgcm = AESGCM(key_bytes[:32])

    def encrypt(self, plaintext: str) -> str:
        nonce = secrets.token_bytes(12)
        ct = self.aesgcm.encrypt(nonce, plaintext.encode(), None)
        return base64.b64encode(nonce + ct).decode()

    def decrypt(self, encrypted: str) -> str:
        data = base64.b64decode(encrypted)
        nonce, ct = data[:12], data[12:]
        return self.aesgcm.decrypt(nonce, ct, None).decode()


encryption = EncryptionService()


# ─── License Key Generation ───

def generate_license_key() -> str:
    parts = [secrets.token_hex(2).upper() for _ in range(4)]
    return f"FLORA-{'-'.join(parts)}"


def hash_license_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()


# ─── HMAC ───

def generate_hmac(data: str, secret: str) -> str:
    return hmac.new(secret.encode(), data.encode(), hashlib.sha256).hexdigest()


def verify_hmac(data: str, secret: str, expected: str) -> bool:
    return hmac.compare_digest(generate_hmac(data, secret), expected)


# ─── Device Fingerprint ───

def get_device_fingerprint() -> str:
    import platform
    components = [platform.node(), platform.machine(), platform.processor()]
    raw = "|".join(components)
    return hashlib.sha256(raw.encode()).hexdigest()
