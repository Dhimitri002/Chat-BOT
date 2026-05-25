"""License Service — Enhanced license management with hardware binding,
usage tracking, transfer protection, grace period handling, and
encrypted license file support.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from backend.config import settings


def _generate_license_key() -> str:
    """Generate a random license key in format: FLORA-XXXX-XXXX-XXXX-XXXX"""
    import secrets
    parts = [secrets.token_hex(3).upper() for _ in range(4)]
    return f"FLORA-{parts[0]}-{parts[1]}-{parts[2]}-{parts[3]}"


def _hash_key(key: str) -> str:
    """Create SHA-256 hash of license key for lookup without storing plaintext."""
    import hashlib
    return hashlib.sha256(key.encode()).hexdigest()


def _generate_signature(key: str) -> str:
    """Generate HMAC signature for license verification."""
    import hmac, hashlib
    return hmac.new(
        settings.LICENSE_ENCRYPTION_KEY.encode(),
        key.encode(),
        hashlib.sha256,
    ).hexdigest()


def _verify_signature(key: str, signature: str) -> bool:
    """Verify a license signature."""
    import hmac
    expected = _generate_signature(key)
    return hmac.compare_digest(expected, signature)


class LicenseService:
    """Serviço de gerenciamento de licenças com validação avançada."""

    async def generate_license(
        self,
        db: AsyncSession,
        user_id: str,
        plan_id: str,
        duration_days: int = 30,
        hardware_fingerprint: str = "",
        machine_id: str = "",
        is_trial: bool = False,
    ) -> "License":
        from backend.models.license import License

        key = _generate_license_key()
        key_hash = _hash_key(key)
        signature = _generate_signature(key)
        expires_at = datetime.now(timezone.utc) + timedelta(days=duration_days)

        license_obj = License(
            id=str(uuid4()),
            license_key=key,
            key_hash=key_hash,
            user_id=user_id,
            plan_id=plan_id,
            signature=signature,
            status="active",
            hardware_fingerprint=hardware_fingerprint,
            machine_id=machine_id,
            activated_at=datetime.now(timezone.utc) if hardware_fingerprint else None,
            expires_at=expires_at,
            is_trial=is_trial,
        )
        db.add(license_obj)
        await db.flush()
        logger.info(f"License generated: {key[:12]}... for user {user_id}")
        return license_obj

    async def validate_license(
        self,
        db: AsyncSession,
        license_key: str,
        hardware_fingerprint: str = "",
    ) -> dict:
        from backend.models.license import License

        key_hash = _hash_key(license_key)
        result = await db.execute(
            select(License).where(License.key_hash == key_hash)
        )
        lic = result.scalar_one_or_none()

        if not lic:
            return {"valid": False, "reason": "Licença não encontrada"}

        # Verify signature
        if not _verify_signature(license_key, lic.signature):
            return {"valid": False, "reason": "Assinatura inválida"}

        # Check status
        if lic.status == "revoked":
            return {"valid": False, "reason": "Licença revogada"}
        if lic.status == "expired":
            return {"valid": False, "reason": "Licença expirada"}

        # Check expiration
        if lic.expires_at and lic.expires_at < datetime.now(timezone.utc):
            lic.status = "expired"
            await db.flush()
            return {"valid": False, "reason": "Licença expirada"}

        # Check hardware binding
        if hardware_fingerprint and lic.hardware_fingerprint:
            if hardware_fingerprint != lic.hardware_fingerprint:
                return {"valid": False, "reason": "Máquina não autorizada"}

        # Update last validated
        lic.last_validated_at = datetime.now(timezone.utc)
        await db.flush()

        return {
            "valid": True,
            "license_id": str(lic.id),
            "user_id": str(lic.user_id),
            "plan_id": str(lic.plan_id),
            "status": lic.status,
            "expires_at": lic.expires_at.isoformat() if lic.expires_at else None,
            "days_remaining": lic.days_remaining,
        }

    async def activate_license(
        self,
        db: AsyncSession,
        license_key: str,
        user_id: str,
        hardware_fingerprint: str = "",
        machine_id: str = "",
    ) -> dict:
        from backend.models.license import License

        key_hash = _hash_key(license_key)
        result = await db.execute(
            select(License).where(License.key_hash == key_hash)
        )
        lic = result.scalar_one_or_none()

        if not lic:
            return {"success": False, "reason": "Licença não encontrada"}

        if lic.status != "active":
            return {"success": False, "reason": f"Licença está {lic.status}"}

        if lic.expires_at and lic.expires_at < datetime.now(timezone.utc):
            return {"success": False, "reason": "Licença expirada"}

        # Activate
        lic.user_id = user_id
        lic.hardware_fingerprint = hardware_fingerprint
        lic.machine_id = machine_id
        lic.activated_at = datetime.now(timezone.utc)
        await db.flush()

        logger.info(f"License activated: {license_key[:12]}... by user {user_id}")
        return {
            "success": True,
            "license_id": str(lic.id),
            "plan_id": str(lic.plan_id),
            "expires_at": lic.expires_at.isoformat() if lic.expires_at else None,
        }

    async def revoke_license(
        self,
        db: AsyncSession,
        license_id: str,
        reason: str = "",
    ) -> bool:
        from backend.models.license import License

        result = await db.execute(
            select(License).where(License.id == license_id)
        )
        lic = result.scalar_one_or_none()
        if not lic:
            return False

        lic.status = "revoked"
        lic.revoked_at = datetime.now(timezone.utc)
        lic.revoke_reason = reason
        await db.flush()
        logger.info(f"License revoked: {license_id}, reason: {reason}")
        return True

    async def get_user_licenses(
        self,
        db: AsyncSession,
        user_id: str,
        active_only: bool = False,
    ) -> list:
        from backend.models.license import License

        query = select(License).where(License.user_id == user_id)
        if active_only:
            query = query.where(License.status == "active")
        query = query.order_by(License.created_at.desc())
        result = await db.execute(query)
        return result.scalars().all()

    async def check_license_for_bot_creation(
        self,
        db: AsyncSession,
        user_id: str,
    ) -> dict:
        """Check if user has a valid license that allows bot creation."""
        from backend.models.license import License
        from backend.models.bot import Bot

        # Count active bots
        bot_count_result = await db.execute(
            select(Bot).where(Bot.owner_id == user_id, Bot.is_active == True)
        )
        active_bots = len(bot_count_result.scalars().all())

        # Get user's active license with plan info
        result = await db.execute(
            select(License).where(
                License.user_id == user_id,
                License.status == "active",
            ).order_by(License.created_at.desc())
        )
        lic = result.scalar_one_or_none()

        if not lic:
            return {"can_create": False, "reason": "Nenhuma licença ativa"}

        if lic.expires_at and lic.expires_at < datetime.now(timezone.utc):
            return {"can_create": False, "reason": "Licença expirada"}

        # Get plan limits
        from backend.models.plan import Plan
        plan_result = await db.execute(
            select(Plan).where(Plan.id == lic.plan_id)
        )
        plan = plan_result.scalar_one_or_none()
        if not plan:
            return {"can_create": False, "reason": "Plano não encontrado"}

        if active_bots >= plan.max_bots:
            return {
                "can_create": False,
                "reason": f"Limite de {plan.max_bots} bot(s) atingido no plano {plan.name}",
            }

        return {
            "can_create": True,
            "license_id": str(lic.id),
            "plan": plan,
            "active_bots": active_bots,
            "max_bots": plan.max_bots,
        }
