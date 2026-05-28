"""
Flora Platform — License Service
==================================
Handles license creation, validation, activation, deactivation,
transfer, renewal, concurrent session limiting, and audit trail.
"""
from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.core.encryption import (
    generate_hardware_fingerprint,
    generate_license_key,
    validate_license_key_format,
    verify_hardware_fingerprint,
)
from backend.models.audit_log import AuditAction, AuditLog, AuditSeverity
from backend.models.license import License, LicenseStatus, LicenseTransferHistory
from backend.models.plan import Plan
from backend.models.user import User

logger = logging.getLogger(__name__)


# ─── Concurrent Session Tracker ───────────────────────────

@dataclass
class _SessionEntry:
    """Track an active license session."""
    session_id: str
    created_at: float
    last_activity: float
    hardware_fingerprint: Optional[str] = None


class LicenseSessionManager:
    """
    Manage concurrent sessions per license.

    Enforces max concurrent sessions per license.
    """

    def __init__(self, max_concurrent: int = 1):
        self._max_concurrent = max_concurrent
        self._sessions: dict[int, dict[str, _SessionEntry]] = defaultdict(dict)

    def get_active_count(self, license_id: int) -> int:
        """Get the number of active sessions for a license."""
        self._cleanup(license_id)
        return len(self._sessions.get(license_id, {}))

    def can_create_session(self, license_id: int) -> bool:
        """Check if a new session can be created."""
        return self.get_active_count(license_id) < self._max_concurrent

    def create_session(
        self,
        license_id: int,
        session_id: str,
        hardware_fingerprint: Optional[str] = None,
    ) -> bool:
        """
        Create a new session for a license.

        Returns:
            True if session was created, False if limit reached.
        """
        import time
        self._cleanup(license_id)

        if len(self._sessions[license_id]) >= self._max_concurrent:
            return False

        now = time.monotonic()
        self._sessions[license_id][session_id] = _SessionEntry(
            session_id=session_id,
            created_at=now,
            last_activity=now,
            hardware_fingerprint=hardware_fingerprint,
        )
        return True

    def end_session(self, license_id: int, session_id: str) -> None:
        """End a session."""
        if license_id in self._sessions and session_id in self._sessions[license_id]:
            del self._sessions[license_id][session_id]

    def _cleanup(self, license_id: int) -> None:
        """Remove stale sessions (inactive for > 4 hours)."""
        import time
        now = time.monotonic()
        stale_threshold = 4 * 3600  # 4 hours
        sessions = self._sessions.get(license_id, {})
        stale = [
            sid for sid, entry in sessions.items()
            if now - entry.last_activity > stale_threshold
        ]
        for sid in stale:
            del sessions[sid]


# Global session manager
_session_manager = LicenseSessionManager(
    max_concurrent=settings.LICENSE_MAX_MACHINES,
)


# ─── Custom Exceptions ────────────────────────────────────


class LicenseError(Exception):
    """Base license error."""
    def __init__(self, message: str, code: str = "LICENSE_ERROR"):
        self.message = message
        self.code = code
        super().__init__(message)


class LicenseNotFoundError(LicenseError):
    def __init__(self):
        super().__init__("Licenca nao encontrada", "LICENSE_NOT_FOUND")


class LicenseExpiredError(LicenseError):
    def __init__(self):
        super().__init__("Licenca expirada", "LICENSE_EXPIRED")


class LicenseRevokedError(LicenseError):
    def __init__(self):
        super().__init__("Licenca revogada", "LICENSE_REVOKED")


class LicenseKeyInvalidError(LicenseError):
    def __init__(self):
        super().__init__("Chave de licenca invalida", "LICENSE_KEY_INVALID")


class LicenseAlreadyActiveError(LicenseError):
    def __init__(self):
        super().__init__("Usuario ja possui uma licenca ativa", "LICENSE_ALREADY_ACTIVE")


class LicenseLimitReachedError(LicenseError):
    def __init__(self):
        super().__init__("Limite de sessoes concorrentes atingido", "LIMIT_REACHED")


class LicenseTransferLimitError(LicenseError):
    def __init__(self):
        super().__init__("Limite de transferencias atingido", "TRANSFER_LIMIT")


# ─── License Service ──────────────────────────────────────


class LicenseService:
    """License management service for Flora Platform."""

    def __init__(self, db: AsyncSession):
        self._db = db

    # ─── License Creation (Admin) ──────────────────────────────

    async def create_license(
        self,
        plan_id: int,
        user_id: int,
        duration_days: int = 30,
        license_key: Optional[str] = None,
        hardware_fingerprint: Optional[str] = None,
        max_machines: Optional[int] = None,
        auto_renew: bool = False,
        created_by: Optional[int] = None,
    ) -> License:
        """
        Create a new license for a user.

        Args:
            plan_id: Plan ID for this license
            user_id: User ID to assign the license
            duration_days: License duration in days
            license_key: Optional custom key (auto-generated if not provided)
            hardware_fingerprint: Optional hardware binding
            max_machines: Override max concurrent machines
            auto_renew: Enable auto-renewal
            created_by: Admin user ID who created it

        Returns:
            Created License object
        """
        now = datetime.now(timezone.utc)

        if license_key is None:
            license_key = generate_license_key()

        license_obj = License(
            license_key=license_key,
            user_id=user_id,
            plan_id=plan_id,
            status=LicenseStatus.ACTIVE,
            activated_at=now,
            expires_at=now + timedelta(days=duration_days),
            hardware_fingerprint=hardware_fingerprint,
            max_machines=max_machines or settings.LICENSE_MAX_MACHINES,
            auto_renew=auto_renew,
        )

        self._db.add(license_obj)
        await self._db.flush()

        await self._log_audit(
            action=AuditAction.LICENSE_ACTIVATED,
            severity=AuditSeverity.INFO,
            user_id=str(user_id),
            description=f"Licenca criada: {license_key[:12]}... Plano: {plan_id}",
            actor_id=str(created_by) if created_by else None,
            metadata_={"license_id": license_obj.id, "plan_id": plan_id, "duration_days": duration_days},
        )

        logger.info(
            "LICENSE_CREATED id=%s user_id=%s plan_id=%s",
            license_obj.id,
            user_id,
            plan_id,
        )
        return license_obj

    # ─── License Validation ────────────────────────────────────

    async def validate_license(
        self,
        license_key: str,
        hardware_fingerprint: Optional[str] = None,
    ) -> License:
        """
        Validate a license key.

        Checks:
            - Key format and checksum
            - Existence in database
            - Status (active, expired, revoked, suspended)
            - Expiry date
            - Grace period
            - Hardware binding (if configured)

        Args:
            license_key: The license key to validate
            hardware_fingerprint: Optional hardware fingerprint to check

        Returns:
            Validated License object

        Raises:
            LicenseKeyInvalidError: If key format is invalid
            LicenseNotFoundError: If key doesn't exist in DB
            LicenseExpiredError: If license is expired
            LicenseRevokedError: If license is revoked
        """
        # Validate key format and checksum
        if not validate_license_key_format(license_key):
            raise LicenseKeyInvalidError()

        # Find the license
        result = await self._db.execute(
            select(License).where(License.license_key == license_key)
        )
        license_obj = result.scalar_one_or_none()

        if license_obj is None:
            raise LicenseNotFoundError()

        # Check status
        if license_obj.status == LicenseStatus.REVOKED:
            raise LicenseRevokedError()

        if license_obj.status == LicenseStatus.SUSPENDED:
            raise LicenseError("Licenca suspensa", "LICENSE_SUSPENDED")

        now = datetime.now(timezone.utc)

        # Check expiry
        if license_obj.expires_at and license_obj.expires_at < now:
            grace_period = timedelta(days=settings.LICENSE_GRACE_PERIOD_DAYS)
            if license_obj.expires_at + grace_period < now:
                # Past grace period — update status
                license_obj.status = LicenseStatus.EXPIRED
                await self._db.flush()
                raise LicenseExpiredError()
            else:
                # In grace period — allow but warn
                logger.warning(
                    "LICENSE_GRACE_PERIOD license_id=%s expires_at=%s",
                    license_obj.id,
                    license_obj.expires_at,
                )

        # Check hardware binding
        if license_obj.hardware_fingerprint and hardware_fingerprint:
            if not verify_hardware_fingerprint(license_obj.hardware_fingerprint, hardware_fingerprint):
                raise LicenseError(
                    "Fingerprint de hardware nao corresponde",
                    "HARDWARE_MISMATCH",
                )

        return license_obj

    # ─── License Activation ────────────────────────────────────

    async def activate_license(
        self,
        license_key: str,
        user_id: int,
        hardware_fingerprint: Optional[str] = None,
    ) -> License:
        """
        Activate a license for a user.

        Args:
            license_key: License key to activate
            user_id: User ID to activate for
            hardware_fingerprint: Optional hardware fingerprint for binding

        Returns:
            Activated License object

        Raises:
            LicenseKeyInvalidError: If key format is invalid
            LicenseNotFoundError: If key doesn't exist
            LicenseAlreadyActiveError: If user already has an active license
        """
        # Validate the license first
        license_obj = await self.validate_license(license_key, hardware_fingerprint)

        # Check if user already has an active license
        existing = await self._db.execute(
            select(License).where(
                License.user_id == user_id,
                License.status == LicenseStatus.ACTIVE,
            )
        )
        if existing.scalar_one_or_none():
            raise LicenseAlreadyActiveError()

        # Activate
        now = datetime.now(timezone.utc)
        license_obj.user_id = user_id
        license_obj.status = LicenseStatus.ACTIVE
        license_obj.activated_at = now

        if hardware_fingerprint:
            license_obj.hardware_fingerprint = hardware_fingerprint

        await self._db.flush()

        await self._log_audit(
            action=AuditAction.LICENSE_ACTIVATED,
            severity=AuditSeverity.INFO,
            user_id=str(user_id),
            description=f"Licenca ativada: {license_key[:12]}...",
            metadata_={"license_id": license_obj.id},
        )

        logger.info("LICENSE_ACTIVATED id=%s user_id=%s", license_obj.id, user_id)
        return license_obj

    # ─── License Deactivation ──────────────────────────────────

    async def deactivate_license(
        self,
        license_id: int,
        user_id: int,
        reason: str = "",
    ) -> License:
        """
        Deactivate a license.

        Args:
            license_id: License ID
            user_id: User ID (for verification)
            reason: Reason for deactivation

        Returns:
            Deactivated License object
        """
        license_obj = await self._get_license_or_raise(license_id)

        if license_obj.user_id != user_id:
            raise LicenseError("Licenca nao pertence a este usuario", "NOT_OWNER")

        license_obj.status = LicenseStatus.INACTIVE
        license_obj.deactivated_at = datetime.now(timezone.utc)

        # End all sessions
        _session_manager._sessions.pop(license_id, None)

        await self._db.flush()

        await self._log_audit(
            action=AuditAction.LICENSE_DEACTIVATED,
            severity=AuditSeverity.INFO,
            user_id=str(user_id),
            description=f"Licenca desativada: {reason}",
            metadata_={"license_id": license_id},
        )

        logger.info("LICENSE_DEACTIVATED id=%s user_id=%s", license_id, user_id)
        return license_obj

    # ─── License Transfer ──────────────────────────────────────

    async def transfer_license(
        self,
        license_id: int,
        from_user_id: int,
        to_user_id: int,
    ) -> License:
        """
        Transfer a license from one user to another.

        Checks transfer limit and records history.

        Args:
            license_id: License ID
            from_user_id: Current owner
            to_user_id: New owner

        Returns:
            Transferred License object

        Raises:
            LicenseTransferLimitError: If transfer limit reached
        """
        license_obj = await self._get_license_or_raise(license_id)

        if license_obj.user_id != from_user_id:
            raise LicenseError("Licenca nao pertence a este usuario", "NOT_OWNER")

        # Check transfer limit
        transfer_count = await self._db.execute(
            select(LicenseTransferHistory).where(
                LicenseTransferHistory.license_id == license_id
            )
        )
        transfer_count = len(transfer_count.scalars().all())

        if transfer_count >= settings.LICENSE_MAX_TRANSFERS:
            raise LicenseTransferLimitError()

        # Record transfer history
        transfer_record = LicenseTransferHistory(
            license_id=license_id,
            from_user_id=from_user_id,
            to_user_id=to_user_id,
            transferred_at=datetime.now(timezone.utc),
        )
        self._db.add(transfer_record)

        # Transfer
        old_user_id = license_obj.user_id
        license_obj.user_id = to_user_id
        license_obj.hardware_fingerprint = None  # Reset hardware binding
        license_obj.activated_at = datetime.now(timezone.utc)

        # End old sessions
        _session_manager._sessions.pop(license_id, None)

        await self._db.flush()

        await self._log_audit(
            action=AuditAction.LICENSE_TRANSFERRED,
            severity=AuditSeverity.INFO,
            user_id=str(to_user_id),
            description=f"Licenca transferida de {old_user_id} para {to_user_id}",
            metadata_={"license_id": license_id, "from_user_id": old_user_id, "to_user_id": to_user_id},
        )

        logger.info(
            "LICENSE_TRANSFERRED id=%s from=%s to=%s",
            license_id,
            old_user_id,
            to_user_id,
        )
        return license_obj

    # ─── License Renewal ───────────────────────────────────────

    async def renew_license(
        self,
        license_id: int,
        additional_days: int = 30,
        user_id: Optional[int] = None,
    ) -> License:
        """
        Renew/extend a license.

        Args:
            license_id: License ID
            additional_days: Days to add
            user_id: Optional user ID for verification

        Returns:
            Renewed License object
        """
        license_obj = await self._get_license_or_raise(license_id)

        if user_id and license_obj.user_id != user_id:
            raise LicenseError("Licenca nao pertence a este usuario", "NOT_OWNER")

        now = datetime.now(timezone.utc)

        # If expired, extend from now; otherwise extend from current expiry
        base_date = max(license_obj.expires_at or now, now)
        license_obj.expires_at = base_date + timedelta(days=additional_days)

        # Reactivate if expired
        if license_obj.status == LicenseStatus.EXPIRED:
            license_obj.status = LicenseStatus.ACTIVE

        await self._db.flush()

        await self._log_audit(
            action=AuditAction.LICENSE_RENEWED,
            severity=AuditSeverity.INFO,
            user_id=str(license_obj.user_id),
            description=f"Licenca renovada por {additional_days} dias",
            metadata_={
                "license_id": license_id,
                "additional_days": additional_days,
                "new_expiry": license_obj.expires_at.isoformat(),
            },
        )

        logger.info(
            "LICENSE_RENEWED id=%s additional_days=%d new_expiry=%s",
            license_id,
            additional_days,
            license_obj.expires_at,
        )
        return license_obj

    # ─── Get User's License ────────────────────────────────────

    async def get_user_license(self, user_id: int) -> Optional[License]:
        """Get the active license for a user."""
        result = await self._db.execute(
            select(License).where(
                License.user_id == user_id,
                License.status == LicenseStatus.ACTIVE,
            )
        )
        return result.scalar_one_or_none()

    # ─── Get License History ───────────────────────────────────

    async def get_license_history(self, license_id: int) -> list[LicenseTransferHistory]:
        """Get transfer history for a license."""
        result = await self._db.execute(
            select(LicenseTransferHistory)
            .where(LicenseTransferHistory.license_id == license_id)
            .order_by(LicenseTransferHistory.transferred_at.desc())
        )
        return list(result.scalars().all())

    # ─── Admin: List All Licenses ──────────────────────────────

    async def list_licenses(
        self,
        status: Optional[LicenseStatus] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[License], int]:
        """
        List licenses with optional filtering.

        Returns:
            (licenses, total_count)
        """
        query = select(License)
        count_query = select(License)

        if status:
            query = query.where(License.status == status)
            count_query = count_query.where(License.status == status)

        # Get total count
        count_result = await self._db.execute(count_query)
        total = len(count_result.scalars().all())

        # Get paginated results
        query = query.order_by(License.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self._db.execute(query)
        licenses = list(result.scalars().all())

        return licenses, total

    # ─── Admin: Revoke License ─────────────────────────────────

    async def revoke_license(
        self,
        license_id: int,
        reason: str = "",
        admin_id: Optional[int] = None,
    ) -> License:
        """Revoke a license (admin only)."""
        license_obj = await self._get_license_or_raise(license_id)

        license_obj.status = LicenseStatus.REVOKED
        license_obj.deactivated_at = datetime.now(timezone.utc)

        # End all sessions
        _session_manager._sessions.pop(license_id, None)

        await self._db.flush()

        await self._log_audit(
            action=AuditAction.LICENSE_REVOKED,
            severity=AuditSeverity.WARNING,
            user_id=str(license_obj.user_id),
            description=f"Licenca revogada: {reason}",
            actor_id=str(admin_id) if admin_id else None,
            metadata_={"license_id": license_id},
        )

        logger.info("LICENSE_REVOKED id=%s reason=%s", license_id, reason)
        return license_obj

    # ─── Concurrent Session Management ─────────────────────────

    async def check_concurrent_sessions(self, license_id: int) -> bool:
        """Check if a new session can be created for this license."""
        return _session_manager.can_create_session(license_id)

    def get_active_session_count(self, license_id: int) -> int:
        """Get the number of active sessions for a license."""
        return _session_manager.get_active_count(license_id)

    # ─── Internal Helpers ──────────────────────────────────────

    async def _get_license_or_raise(self, license_id: int) -> License:
        """Get a license by ID or raise LicenseNotFoundError."""
        result = await self._db.execute(
            select(License).where(License.id == license_id)
        )
        license_obj = result.scalar_one_or_none()

        if license_obj is None:
            raise LicenseNotFoundError()

        return license_obj

    async def _log_audit(
        self,
        action: AuditAction,
        severity: AuditSeverity,
        user_id: Optional[str] = None,
        description: str = "",
        actor_id: Optional[str] = None,
        metadata_: Optional[dict] = None,
    ) -> None:
        """Create an audit log entry."""
        try:
            log_entry = AuditLog(
                user_id=int(user_id) if user_id else None,
                action=action,
                severity=severity,
                description=description,
                metadata_=metadata_ or {},
            )
            self._db.add(log_entry)
            await self._db.flush()
        except Exception as e:
            logger.error("AUDIT_LOG_ERROR: %s", e)
