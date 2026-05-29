"""
Flora Platform — Encryption & License Key Utilities

Provides:
- Fernet symmetric encryption for data at rest
- License key generation: FLORA-XXXX-XXXX-XXXX with checksum
- License key validation with checksum verification
- Hardware fingerprinting for license binding
- PBKDF2 key derivation
- PII data encryption/decryption helpers
"""
from __future__ import annotations

import hashlib
import hmac
import logging
import os
import platform
import re
import secrets
import string
import uuid
from datetime import datetime, timezone
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken

from backend.config import settings

logger = logging.getLogger(__name__)

# ─── Constants ───────────────────────────────────────────────

LICENSE_CHARS = string.ascii_uppercase + string.digits  # A-Z, 0-9
LICENSE_CHAR_EXCLUDE = "0O1LI"  # Exclude ambiguous characters
LICENSE_ALPHABET = "".join(c for c in LICENSE_CHARS if c not in LICENSE_CHAR_EXCLUDE)
LICENSE_SEGMENT_LENGTH = 4
LICENSE_SEGMENTS = 3
LICENSE_PREFIX = "FLORA"
LICENSE_SEPARATOR = "-"


# ─── Fernet Encryption Manager ─────────────────────────────


class FernetEncryptor:
    """Symmetric encryption using Fernet (AES-128-CBC + HMAC-SHA256)."""

    def __init__(self, key: Optional[str] = None):
        """Initialize with a base64-encoded 32-byte key or derive from settings."""
        raw_key = key or settings.ENCRYPTION_KEY
        if not raw_key:
            # Auto-generate a key if none is configured (dev mode)
            logger.warning("ENCRYPTION_KEY not set — generating ephemeral key. "
                           "Set ENCRYPTION_KEY in .env for production.")
            raw_key = Fernet.generate_key().decode()
        if isinstance(raw_key, str):
            import base64
            try:
                # Try to decode as-is (may already be valid base64)
                decoded = base64.urlsafe_b64decode(raw_key)
                if len(decoded) == 32:
                    pass  # valid key
                else:
                    # Not 32 bytes — derive one via SHA-256
                    import hashlib
                    raw_key = base64.urlsafe_b64encode(hashlib.sha256(raw_key.encode()).digest()).decode()
            except Exception:
                # Not valid base64 — hash the raw string to derive a key
                import hashlib
                raw_key = base64.urlsafe_b64encode(hashlib.sha256(raw_key.encode()).digest()).decode()
        self._fernet = Fernet(raw_key)

    @staticmethod
    def generate_key() -> str:
        """Generate a new Fernet key."""
        return Fernet.generate_key().decode()

    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt a plaintext string.

        Returns base64-encoded ciphertext.
        """
        if not plaintext:
            return ""
        return self._fernet.encrypt(plaintext.encode("utf-8")).decode("utf-8")

    def decrypt(self, ciphertext: str) -> str:
        """
        Decrypt a Fernet-encrypted ciphertext string.

        Raises:
            ValueError: If the token is invalid or tampered with.
        """
        if not ciphertext:
            return ""
        try:
            return self._fernet.decrypt(ciphertext.encode("utf-8")).decode("utf-8")
        except InvalidToken:
            raise ValueError("Token de criptografia inválido ou adulterado")

    def encrypt_dict(self, data: dict) -> str:
        """Encrypt a dictionary as JSON string."""
        import json
        return self.encrypt(json.dumps(data, default=str))

    def decrypt_dict(self, ciphertext: str) -> dict:
        """Decrypt back to dictionary."""
        import json
        return json.loads(self.decrypt(ciphertext))


# ─── PII Data Helpers ─────────────────────────────────────

_fernet_encryptor = FernetEncryptor()


def encrypt_pii(plaintext: str) -> str:
    """Encrypt PII data (email, phone, document) for storage."""
    return _fernet_encryptor.encrypt(plaintext)


def decrypt_pii(ciphertext: str) -> str:
    """Decrypt PII data from storage."""
    return _fernet_encryptor.decrypt(ciphertext)


def mask_email(email: str) -> str:
    """Mask email for display: j***@example.com."""
    if not email or "@" not in email:
        return "***"
    local, domain = email.rsplit("@", 1)
    if len(local) <= 2:
        masked = local[0] + "***"
    else:
        masked = local[0] + "***" + local[-1]
    return f"{masked}@{domain}"


def mask_phone(phone: str) -> str:
    """Mask phone for display: +55*****1234."""
    digits = re.sub(r"\D", "", phone)
    if len(digits) < 4:
        return "***"
    return f"{'*' * (len(digits) - 4)}{digits[-4:]}"


# ─── PBKDF2 Key Derivation ────────────────────────────────


def derive_key_from_password(
    password: str,
    salt: Optional[bytes] = None,
    iterations: int = 600_000,
    key_length: int = 32,
) -> tuple[bytes, bytes]:
    """
    Derive a cryptographic key from a password using PBKDF2-HMAC-SHA256.

    Returns:
        (derived_key, salt) tuple
    """
    if salt is None:
        salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations, dklen=key_length)
    return dk, salt


def verify_derived_key(password: str, expected_key: bytes, salt: bytes, iterations: int = 600_000) -> bool:
    """Verify a password against a derived key."""
    dk, _ = derive_key_from_password(password, salt=salt, iterations=iterations)
    return hmac.compare_digest(dk, expected_key)


# ─── License Key Generation & Validation ───────────────────


def _checksum_segment(segment: str, secret: Optional[str] = None) -> str:
    """
    Generate a single-char checksum for a license segment.

    Uses HMAC-SHA256 truncated to one character from LICENSE_ALPHABET.
    """
    key = (secret or settings.LICENSE_SECRET or settings.SECRET_KEY).encode("utf-8")
    h = hmac.new(key, segment.encode("utf-8"), hashlib.sha256).digest()
    return LICENSE_ALPHABET[h[0] % len(LICENSE_ALPHABET)]


def generate_license_key(segment_length: int = LICENSE_SEGMENT_LENGTH) -> str:
    """
    Generate a unique license key: FLORA-XXXX-XXXX-XXXX-C

    Format:
        FLORA-{seg1}-{seg2}-{seg3}-{checksum}

    Where:
        - Each segment is random characters from LICENSE_ALPHABET
        - Checksum is an HMAC-based character for validation
        - Total length: FLORA-XXXX-XXXX-XXXX-X

    Returns:
        License key string (e.g., "FLORA-K8N3-P7R2-X9M7-A")
    """
    segments: list[str] = []
    for _ in range(LICENSE_SEGMENTS):
        seg = "".join(secrets.choice(LICENSE_ALPHABET) for _ in range(segment_length))
        segments.append(seg)

    # Build partial key for checksum computation (without prefix to keep it short)
    core = LICENSE_SEPARATOR.join(segments)
    checksum = _checksum_segment(core)

    return f"{LICENSE_PREFIX}{LICENSE_SEPARATOR}{core}{LICENSE_SEPARATOR}{checksum}"


def validate_license_key_format(key: str, secret: Optional[str] = None) -> bool:
    """
    Validate the format and checksum of a license key.

    Checks:
        - Correct prefix (FLORA)
        - Correct number of segments (3)
        - Each segment has correct length
        - All characters are from LICENSE_ALPHABET
        - Checksum matches

    Returns:
        True if valid, False otherwise.
    """
    if not key or not isinstance(key, str):
        return False

    parts = key.split(LICENSE_SEPARATOR)
    # Expected: [FLORA, seg1, seg2, seg3, checksum] = 5 parts
    if len(parts) != LICENSE_SEGMENTS + 2:
        return False

    prefix = parts[0]
    if prefix != LICENSE_PREFIX:
        return False

    # Validate each segment
    segments = parts[1 : 1 + LICENSE_SEGMENTS]
    for seg in segments:
        if len(seg) != segment_length_static():
            return False
        if not all(c in LICENSE_ALPHABET for c in seg):
            return False

    # Validate checksum
    expected_checksum = _checksum_segment(LICENSE_SEPARATOR.join(segments), secret or settings.LICENSE_SECRET)
    actual_checksum = parts[-1]

    return hmac.compare_digest(expected_checksum, actual_checksum)


def segment_length_static() -> int:
    """Return the configured segment length."""
    return LICENSE_SEGMENT_LENGTH


# ─── Hardware Fingerprinting ──────────────────────────────


def generate_hardware_fingerprint(
    machine_id: Optional[str] = None,
    mac_address: Optional[str] = None,
    hostname: Optional[str] = None,
) -> str:
    """
    Generate a hardware fingerprint string for license binding.

    Combines multiple system identifiers to create a unique fingerprint.

    Args:
        machine_id: System machine ID (e.g., from platform.node() or uuid.getnode())
        mac_address: MAC address string
        hostname: System hostname

    Returns:
        SHA-256 hash string representing the hardware fingerprint.
    """
    parts: list[str] = []

    if machine_id:
        parts.append(machine_id)
    else:
        parts.append(str(uuid.getnode()))  # Falls back to MAC as int

    if mac_address:
        parts.append(mac_address)

    if hostname:
        parts.append(hostname)
    else:
        parts.append(platform.node())

    # Add stable platform identifiers
    parts.append(platform.machine())
    parts.append(platform.system())

    combined = "|".join(parts)
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()


def verify_hardware_fingerprint(stored_fingerprint: str, current_fingerprint: str) -> bool:
    """
    Verify if the current hardware fingerprint matches the stored one.

    Uses constant-time comparison to prevent timing attacks.
    """
    return hmac.compare_digest(stored_fingerprint, current_fingerprint)


# ─── Data Hashing Utilities ───────────────────────────────


def hash_sensitive_value(value: str, salt: Optional[str] = None) -> str:
    """
    One-way hash for sensitive values that don't need decryption.

    Uses SHA-256 with optional salt.
    """
    combined = f"{salt or settings.SECRET_KEY}{value}"
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()


def generate_secure_token(length: int = 32) -> str:
    """Generate a cryptographically secure random token."""
    return secrets.token_urlsafe(length)


# ─── Module-Level Convenience ─────────────────────────────

_default_encryptor = None


def get_encryptor() -> FernetEncryptor:
    """Get the module-level Fernet encryptor singleton."""
    global _default_encryptor
    if _default_encryptor is None:
        _default_encryptor = FernetEncryptor()
    return _default_encryptor
