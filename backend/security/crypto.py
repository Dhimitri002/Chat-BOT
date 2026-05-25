"""
Flora Platform — Cryptographic Utilities
=========================================
AES-256-GCM encryption for sensitive configs and credentials.
RSA + Ed25519 digital signatures for license signing/verification.
"""

import base64
import hashlib
import hmac
import json
import logging
import os
import secrets
import struct
import time
from datetime import datetime, timezone
from typing import Any, Optional

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey,
        Ed25519PublicKey,
    )
    from cryptography.hazmat.primitives.asymmetric import rsa, padding
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.exceptions import InvalidSignature
    HAS_CRYPTOGRAPHY = True
except ImportError:
    HAS_CRYPTOGRAPHY = False

logger = logging.getLogger(__name__)


class CryptoManager:
    """
    AES-256-GCM encryption manager for sensitive data at rest.

    Used to encrypt:
    - Bot API keys and credentials
    - WhatsApp session tokens
    - User payment information
    - License files
    """

    def __init__(self, master_key: Optional[str] = None):
        """
        Initialize with a master key.

        Args:
            master_key: Base64-encoded 32-byte key, or raw string.
                        If None, generates a new key (for testing only).
        """
        if master_key:
            try:
                self._key = base64.b64decode(master_key)
            except Exception:
                self._key = hashlib.sha256(master_key.encode()).digest()
        else:
            self._key = AESGCM.generate_key(bit_length=256)
            logger.warning("CryptoManager: no master key provided, generated ephemeral key")

        if len(self._key) not in (16, 24, 32):
            self._key = hashlib.sha256(self._key).digest()

        self._aesgcm = AESGCM(self._key)

    @property
    def key_b64(self) -> str:
        """Return the key as base64 for storage."""
        return base64.b64encode(self._key).decode()

    def encrypt(self, plaintext: str, associated_data: Optional[bytes] = None) -> str:
        """
        Encrypt a string using AES-256-GCM.

        Returns base64(nonce + ciphertext + tag).
        """
        nonce = os.urandom(12)
        ciphertext = self._aesgcm.encrypt(
            nonce,
            plaintext.encode("utf-8"),
            associated_data,
        )
        # nonce (12 bytes) + ciphertext+tag
        combined = nonce + ciphertext
        return base64.b64encode(combined).decode()

    def decrypt(self, encrypted: str, associated_data: Optional[bytes] = None) -> str:
        """
        Decrypt an AES-256-GCM encrypted string.
        """
        try:
            combined = base64.b64decode(encrypted)
            nonce = combined[:12]
            ciphertext = combined[12:]
            plaintext = self._aesgcm.decrypt(nonce, ciphertext, associated_data)
            return plaintext.decode("utf-8")
        except Exception as e:
            logger.error(f"CryptoManager.decrypt failed: {e}")
            raise ValueError("Falha ao descriptografar dados") from e

    def encrypt_dict(self, data: dict, associated_data: Optional[bytes] = None) -> str:
        """Encrypt a dictionary as JSON."""
        return self.encrypt(json.dumps(data, default=str), associated_data)

    def decrypt_dict(self, encrypted: str, associated_data: Optional[bytes] = None) -> dict:
        """Decrypt JSON data back to a dictionary."""
        return json.loads(self.decrypt(encrypted, associated_data))

    @staticmethod
    def hash_data(data: str, salt: Optional[str] = None) -> str:
        """Create a SHA-256 hash of data with optional salt."""
        if salt:
            data = salt + data
        return hashlib.sha256(data.encode()).hexdigest()

    @staticmethod
    def hmac_sign(data: str, key: str) -> str:
        """Create HMAC-SHA256 signature."""
        return hmac.new(
            key.encode(),
            data.encode(),
            hashlib.sha256,
        ).hexdigest()

    @staticmethod
    def hmac_verify(data: str, key: str, signature: str) -> bool:
        """Verify HMAC-SHA256 signature."""
        expected = CryptoManager.hmac_sign(data, key)
        return hmac.compare_digest(expected, signature)

    @staticmethod
    def generate_token(length: int = 32) -> str:
        """Generate a secure random token."""
        return secrets.token_urlsafe(length)

    @staticmethod
    def generate_api_key(prefix: str = "flora") -> str:
        """Generate an API key with prefix."""
        random_part = secrets.token_hex(24)
        return f"{prefix}_{random_part}"


class LicenseSigner:
    """
    Digital signature manager for license files.

    Supports two modes:
    - HMAC mode (default): Fast, symmetric, uses a secret key
    - RSA/Ed25519 mode: Asymmetric, for offline verification
    """

    def __init__(self, secret_key: Optional[str] = None):
        self._secret_key = secret_key or CryptoManager.generate_token(48)
        self._private_key = None
        self._public_key = None

        if HAS_CRYPTOGRAPHY:
            try:
                self._private_key = Ed25519PrivateKey.generate()
                self._public_key = self._private_key.public_key()
                logger.info("LicenseSigner: Ed25519 keypair generated")
            except Exception as e:
                logger.warning(f"LicenseSigner: Ed25519 init failed, using HMAC: {e}")

    @property
    def public_key_pem(self) -> Optional[str]:
        """Export public key in PEM format for distribution."""
        if self._public_key:
            return self._public_key.public_bytes(
                serialization.Encoding.PEM,
                serialization.PublicFormat.SubjectPublicKeyInfo,
            ).decode()
        return None

    @property
    def private_key_pem(self) -> Optional[str]:
        """Export private key in PEM format (store securely!)."""
        if self._private_key:
            return self._private_key.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.PKCS8,
                serialization.NoEncryption(),
            ).decode()
        return None

    def load_private_key(self, pem_data: str) -> None:
        """Load a private key from PEM."""
        if not HAS_CRYPTOGRAPHY:
            raise RuntimeError("cryptography library not installed")
        self._private_key = serialization.load_pem_private_key(
            pem_data.encode(), password=None
        )
        self._public_key = self._private_key.public_key()

    def load_public_key(self, pem_data: str) -> None:
        """Load a public key from PEM for verification."""
        if not HAS_CRYPTOGRAPHY:
            raise RuntimeError("cryptography library not installed")
        self._public_key = serialization.load_pem_public_key(pem_data.encode())

    def sign_license(self, license_data: dict) -> str:
        """
        Sign license data.

        Returns base64 signature string.
        """
        payload = json.dumps(license_data, sort_keys=True, default=str)

        if self._private_key and HAS_CRYPTOGRAPHY:
            signature = self._private_key.sign(payload.encode())
            return f"ed25519:{base64.b64encode(signature).decode()}"
        else:
            sig = CryptoManager.hmac_sign(payload, self._secret_key)
            return f"hmac:{sig}"

    def verify_license(self, license_data: dict, signature: str) -> bool:
        """Verify a license signature."""
        payload = json.dumps(license_data, sort_keys=True, default=str)

        if signature.startswith("ed25519:") and self._public_key and HAS_CRYPTOGRAPHY:
            try:
                sig_bytes = base64.b64decode(signature[8:])
                self._public_key.verify(sig_bytes, payload.encode())
                return True
            except InvalidSignature:
                return False
            except Exception as e:
                logger.error(f"Ed25519 verify error: {e}")
                return False
        elif signature.startswith("hmac:"):
            expected = CryptoManager.hmac_sign(payload, self._secret_key)
            return hmac.compare_digest(expected, signature[5:])
        else:
            logger.error(f"Unknown signature format: {signature[:20]}")
            return False

    @staticmethod
    def generate_license_key(prefix: str = "FLORA") -> str:
        """Generate a license key: PREFIX-XXXX-XXXX-XXXX-XXXX."""
        parts = [secrets.token_hex(3).upper() for _ in range(4)]
        return f"{prefix}-{parts[0]}-{parts[1]}-{parts[2]}-{parts[3]}"
