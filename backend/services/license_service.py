"""License Service - Serviço de gerenciamento de licenças com validação online."""
from datetime import datetime, timedelta
from typing import Optional
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.license_manager import LicenseManager
from backend.models.license import License
from backend.models.plan import Plan
from backend.config import settings


class LicenseService:
    """Serviço de gerenciamento de licenças."""

    def __init__(self):
        self.license_manager = LicenseManager()

    async def generate_license(
        self, db: AsyncSession, user_id: str, plan_id: str, duration_days: int = 30
    ) -> License:
        """Gera uma nova licença assinada."""
        # Verificar se plano existe
        plan_result = await db.execute(select(Plan).where(Plan.id == plan_id))
        plan = plan_result.scalar_one_or_none()
        if not plan:
            raise ValueError("Plano não encontrado")

        # Gerar chave de licença
        license_key = self.license_manager.generate_license_key(
            user_id=user_id,
            plan_id=plan_id,
            duration_days=duration_days,
        )

        # Assinar licença
        signature = self.license_manager.sign_license({
            "user_id": user_id,
            "plan_id": plan_id,
            "license_key": license_key,
            "duration_days": duration_days,
        })

        # Criar registro no banco
        now = datetime.utcnow()
        license_record = License(
            id=str(uuid4()),
            user_id=user_id,
            plan_id=plan_id,
            license_key=license_key,
            signature=signature,
            status="active",
            activated_at=now,
            expires_at=now + timedelta(days=duration_days),
        )
        db.add(license_record)
        await db.commit()
        await db.refresh(license_record)
        return license_record

    async def activate_license(
        self, db: AsyncSession, user_id: str, license_key: str
    ) -> License:
        """Ativa uma licença para um usuário."""
        # Validar assinatura
        validation = self.license_manager.validate_license(license_key)
        if not validation.get("valid"):
            raise ValueError("Licença inválida ou expirada")

        # Verificar se licença já está em uso
        existing_result = await db.execute(
            select(License).where(License.license_key == license_key)
        )
        existing = existing_result.scalar_one_or_none()

        if existing:
            if existing.status == "active" and existing.user_id != user_id:
                raise ValueError("Licença já está em uso por outro usuário")
            if existing.status == "revoked":
                raise ValueError("Licença foi revogada")
            if existing.status == "expired":
                raise ValueError("Licença expirada")

            # Reativar se for o mesmo usuário
            existing.user_id = user_id
            existing.status = "active"
            existing.activated_at = datetime.utcnow()
            await db.commit()
            await db.refresh(existing)
            return existing

        # Criar nova ativação
        plan_id = validation.get("plan_id", "")
        duration = validation.get("duration_days", 30)

        now = datetime.utcnow()
        license_record = License(
            id=str(uuid4()),
            user_id=user_id,
            plan_id=plan_id,
            license_key=license_key,
            signature=self.license_manager.sign_license({
                "user_id": user_id,
                "plan_id": plan_id,
                "license_key": license_key,
                "duration_days": duration,
            }),
            status="active",
            activated_at=now,
            expires_at=now + timedelta(days=duration),
        )
        db.add(license_record)
        await db.commit()
        await db.refresh(license_record)
        return license_record

    async def validate_license(self, db: AsyncSession, license_key: str) -> dict:
        """Valida uma licença (assinatura + expiração + status no banco)."""
        # Validar assinatura criptográfica
        crypto_validation = self.license_manager.validate_license(license_key)
        if not crypto_validation.get("valid"):
            return {"valid": False, "reason": "invalid_signature"}

        # Verificar no banco
        result = await db.execute(
            select(License).where(License.license_key == license_key)
        )
        license_record = result.scalar_one_or_none()

        if not license_record:
            return {"valid": False, "reason": "not_found"}

        if license_record.status == "revoked":
            return {"valid": False, "reason": "revoked"}

        if license_record.status == "expired":
            return {"valid": False, "reason": "expired"}

        if license_record.expires_at and license_record.expires_at < datetime.utcnow():
            # Atualizar status no banco
            license_record.status = "expired"
            await db.commit()
            return {"valid": False, "reason": "expired"}

        # Buscar plano
        plan_result = await db.execute(
            select(Plan).where(Plan.id == license_record.plan_id)
        )
        plan = plan_result.scalar_one_or_none()

        return {
            "valid": True,
            "license_id": str(license_record.id),
            "user_id": str(license_record.user_id),
            "plan_id": str(license_record.plan_id),
            "plan_name": plan.name if plan else "Unknown",
            "status": license_record.status,
            "expires_at": license_record.expires_at.isoformat() if license_record.expires_at else None,
            "days_remaining": max(0, (license_record.expires_at - datetime.utcnow()).days) if license_record.expires_at else 0,
        }

    async def get_user_licenses(
        self, db: AsyncSession, user_id: str, active_only: bool = False
    ) -> list[License]:
        """Lista licenças de um usuário."""
        query = select(License).where(License.user_id == user_id)
        if active_only:
            query = query.where(License.status == "active")

        result = await db.execute(query.order_by(License.created_at.desc()))
        return result.scalars().all()

    async def get_user_active_license(
        self, db: AsyncSession, user_id: str
    ) -> Optional[License]:
        """Retorna a licença ativa de um usuário."""
        result = await db.execute(
            select(License).where(
                License.user_id == user_id,
                License.status == "active",
            )
        )
        licenses = result.scalars().all()

        # Retornar a que expira mais tarde
        valid_licenses = [
            l for l in licenses
            if l.expires_at and l.expires_at > datetime.utcnow()
        ]

        if not valid_licenses:
            return None

        return max(valid_licenses, key=lambda l: l.expires_at)

    async def revoke_license(
        self, db: AsyncSession, license_id: str, admin_id: str
    ) -> bool:
        """Revoga uma licença (admin only)."""
        result = await db.execute(select(License).where(License.id == license_id))
        license_record = result.scalar_one_or_none()

        if not license_record:
            return False

        license_record.status = "revoked"
        license_record.revoked_at = datetime.utcnow()
        await db.commit()
        return True

    async def deactivate_license(
        self, db: AsyncSession, license_id: str, user_id: str
    ) -> bool:
        """Desativa uma licença (próprio usuário)."""
        result = await db.execute(
            select(License).where(
                License.id == license_id,
                License.user_id == user_id,
            )
        )
        license_record = result.scalar_one_or_none()

        if not license_record:
            return False

        license_record.status = "expired"
        await db.commit()
        return True

    async def check_expired_licenses(self, db: AsyncSession) -> int:
        """Verifica e marca licenças expiradas. Retorna quantidade atualizada."""
        now = datetime.utcnow()
        result = await db.execute(
            select(License).where(
                License.status == "active",
                License.expires_at < now,
            )
        )
        expired = result.scalars().all()

        for license_record in expired:
            license_record.status = "expired"

        if expired:
            await db.commit()

        return len(expired)

    async def get_license_features(self, db: AsyncSession, user_id: str) -> dict:
        """Retorna features disponíveis baseado na licença ativa do usuário."""
        active_license = await self.get_user_active_license(db, user_id)

        if not active_license:
            return {
                "has_access": False,
                "plan": "none",
                "max_bots": 0,
                "max_messages": 0,
                "has_llm": False,
                "has_flora": False,
            }

        plan_result = await db.execute(
            select(Plan).where(Plan.id == active_license.plan_id)
        )
        plan = plan_result.scalar_one_or_none()

        if not plan:
            return {"has_access": False, "plan": "none"}

        return {
            "has_access": True,
            "plan": plan.slug,
            "plan_name": plan.name,
            "max_bots": plan.max_bots,
            "max_messages": plan.max_messages_month,
            "max_commands": plan.max_commands,
            "has_llm": plan.has_llm,
            "has_flora": plan.has_flora,
            "has_media": plan.has_media,
            "has_pdf": plan.has_pdf,
            "has_image": plan.has_image,
            "has_custom_commands": plan.has_custom_commands,
            "has_automations": plan.has_automations,
            "has_webhooks": plan.has_webhooks,
            "has_analytics": plan.has_analytics,
            "expires_at": active_license.expires_at.isoformat() if active_license.expires_at else None,
        }
