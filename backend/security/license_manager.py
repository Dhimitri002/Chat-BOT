"""
Flora Platform — Offline License Manager
=========================================
Handles offline license validation, hardware binding,
expiry checking, and grace periods.
"""

import json
import logging
import os
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from backend.security.crypto import CryptoManager, LicenseSigner

logger = logging.getLogger(__name__)


class LicenseStatus(str, Enum):
    VALID = "valid"
    EXPIRED = "expired"
    INVALID = "invalid"
    HARDWARE_MISMATCH = "hardware_mismatch"
    NOT_FOUND = "not_found"
    REVOKED = "revoked"
    GRACE_PERIOD = "grace_period"
    TRIAL_EXPIRED = "trial_expired"


@dataclass
class LicenseInfo:
    """Parsed license information."""
    license_key: str
    user_id: str
    plan_id: str
    issued_at: str  # ISO format
    expires_at: str  # ISO format
    hardware_fingerprint: str = ""
    machine_id: str = ""
    is_trial: bool = False
    max_bots: int = 1
    max_messages_per_day: int = 100
    features: list = field(default_factory=list)
    signature: str = ""
    grace_period_hours: int = 72

    def to_dict(self) -> dict:
        d = asdict(self)
        # Exclude signature from signed data
        d.pop("signature", None)
        return d

    @property
    def is_expired(self) -> bool:
        try:
            expiry = datetime.fromisoformat(self.expires_at)
            return datetime.now(timezone.utc) > expiry
        except (ValueError, TypeError):
            return True

    @property
    def days_remaining(self) -> int:
        try:
            expiry = datetime.fromisoformat(self.expires_at)
            delta = expiry - datetime.now(timezone.utc)
            return max(0, delta.days)
        except (ValueError, TypeError):
            return 0

    @property
    def is_in_grace_period(self) -> bool:
        """Check if license is past expiry but within grace period."""
        try:
            expiry = datetime.fromisoformat(self.expires_at)
            grace_end = expiry + __import__("datetime").timedelta(hours=self.grace_period_hours)
            now = datetime.now(timezone.utc)
            return expiry < now <= grace_end
        except (ValueError, TypeError):
            return False


class LicenseManager:
    """
    Manages license creation, validation, and offline verification.

    Licenses are encrypted and signed to prevent tampering.
    Hardware fingerprint binding prevents unauthorized transfers.
    """

    def __init__(
        self,
        crypto_manager: Optional[CryptoManager] = None,
        license_signer: Optional[LicenseSigner] = None,
        licenses_path: str = "data/licenses",
    ):
        self._crypto = crypto_manager or CryptoManager()
        self._signer = license_signer or LicenseSigner()
        self._licenses_path = licenses_path
        self._license_cache: dict[str, LicenseInfo] = {}
        self._revoked_keys: set[str] = set()

        os.makedirs(licenses_path, exist_ok=True)

    def create_license(
        self,
        user_id: str,
        plan_id: str,
        duration_days: int = 30,
        hardware_fingerprint: str = "",
        machine_id: str = "",
        is_trial: bool = False,
        max_bots: int = 1,
        max_messages_per_day: int = 100,
        features: Optional[list] = None,
    ) -> LicenseInfo:
        """Create a new signed and encrypted license."""
        now = datetime.now(timezone.utc)
        from datetime import timedelta
        expiry = now + timedelta(days=duration_days)

        info = LicenseInfo(
            license_key=LicenseSigner.generate_license_key("FLORA"),
            user_id=user_id,
            plan_id=plan_id,
            issued_at=now.isoformat(),
            expires_at=expiry.isoformat(),
            hardware_fingerprint=hardware_fingerprint,
            machine_id=machine_id,
            is_trial=is_trial,
            max_bots=max_bots,
            max_messages_per_day=max_messages_per_day,
            features=features or [],
        )

        # Sign the license
        info.signature = self._signer.sign_license(info.to_dict())

        logger.info(
            f"License created: {info.license_key[:12]}... "
            f"user={user_id} plan={plan_id} expiry={expiry.date()}"
        )
        return info

    def save_license(self, license_info: LicenseInfo) -> str:
        """
        Save an encrypted license file to disk.

        Returns the file path.
        """
        filename = f"license_{license_info.user_id}.flora"
        filepath = os.path.join(self._licenses_path, filename)

        data = {
            "license_key": license_info.license_key,
            "user_id": license_info.user_id,
            "plan_id": license_info.plan_id,
            "issued_at": license_info.issued_at,
            "expires_at": license_info.expires_at,
            "hardware_fingerprint": license_info.hardware_fingerprint,
            "machine_id": license_info.machine_id,
            "is_trial": license_info.is_trial,
            "max_bots": license_info.max_bots,
            "max_messages_per_day": license_info.max_messages_per_day,
            "features": license_info.features,
            "signature": license_info.signature,
        }

        encrypted = self._crypto.encrypt_dict(data)
        with open(filepath, "w") as f:
            f.write(encrypted)

        # Cache in memory
        self._license_cache[license_info.license_key] = license_info

        logger.info(f"License saved: {filepath}")
        return filepath

    def load_license(self, user_id: str) -> Optional[LicenseInfo]:
        """Load and decrypt a license file from disk."""
        filename = f"license_{user_id}.flora"
        filepath = os.path.join(self._licenses_path, filename)

        if not os.path.exists(filepath):
            return None

        try:
            with open(filepath, "r") as f:
                encrypted = f.read()

            data = self._crypto.decrypt_dict(encrypted)
            info = LicenseInfo(**data)
            self._license_cache[info.license_key] = info
            return info
        except Exception as e:
            logger.error(f"Failed to load license for user {user_id}: {e}")
            return None

    def validate_license(
        self,
        license_info: LicenseInfo,
        current_hardware_fingerprint: str = "",
        current_machine_id: str = "",
    ) -> LicenseStatus:
        """
        Validate a license comprehensively.

        Checks:
        1. Signature integrity
        2. Expiry date
        3. Hardware fingerprint binding
        4. Revocation list
        5. Grace period
        """
        key_prefix = license_info.license_key[:12]

        # Check revocation
        if license_info.license_key in self._revoked_keys:
            logger.warning(f"License revoked: {key_prefix}...")
            return LicenseStatus.REVOKED

        # Verify signature
        if not self._signer.verify_license(license_info.to_dict(), license_info.signature):
            logger.warning(f"License signature invalid: {key_prefix}...")
            return LicenseStatus.INVALID

        # Check hardware binding (only if hardware data is present)
        if license_info.hardware_fingerprint and current_hardware_fingerprint:
            if license_info.hardware_fingerprint != current_hardware_fingerprint:
                logger.warning(f"Hardware mismatch for license: {key_prefix}...")
                return LicenseStatus.HARDWARE_MISMATCH

        # Check expiry
        if license_info.is_expired:
            if license_info.is_in_grace_period:
                logger.info(f"License in grace period: {key_prefix}...")
                return LicenseStatus.GRACE_PERIOD
            if license_info.is_trial:
                logger.info(f"Trial expired: {key_prefix}...")
                return LicenseStatus.TRIAL_EXPIRED
            logger.info(f"License expired: {key_prefix}...")
            return LicenseStatus.EXPIRED

        logger.debug(f"License valid: {key_prefix}... ({license_info.days_remaining} days left)")
        return LicenseStatus.VALID

    def revoke_license(self, license_key: str) -> None:
        """Add a license key to the revocation list."""
        self._revoked_keys.add(license_key)
        self._license_cache.pop(license_key, None)
        logger.info(f"License revoked: {license_key[:12]}...")

    def deactivate_license_file(self, user_id: str) -> bool:
        """Remove the license file for a user."""
        filename = f"license_{user_id}.flora"
        filepath = os.path.join(self._licenses_path, filename)
        if os.path.exists(filepath):
            os.remove(filepath)
            logger.info(f"License file removed: {filepath}")
            return True
        return False

    def export_public_key(self) -> Optional[str]:
        """Export the public key for offline verification in client apps."""
        return self._signer.public_key_pem
