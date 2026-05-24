"""
License Manager - Sistema de gerenciamento de licenças.
Gera, valida, ativa e revoga licenças com assinatura HMAC.
"""
import hashlib
import hmac
import json
import os
import platform
import re
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.models.license import License
from backend.models.plan import Plan
from backend.models.subscription import Subscription
from backend.models.user import User


def _validate_license_signing_key():
    """Valida que LICENSE_SIGNING_KEY está configurado com valor seguro."""
    key = settings.LICENSE_SIGNING_KEY
    if not key:
        raise ValueError(
            "❌ CRÍTICA: LICENSE_SIGNING_KEY não definida no .env\n"
            "Gere uma chave segura com: python -c \"import secrets; print(secrets.token_hex(64))\"\n"
            "Adicione ao .env: LICENSE_SIGNING_KEY=<chave_gerada>"
        )
    if key == "flora-license-secret-change-me":
        raise ValueError(
            "❌ CRÍTICA: LICENSE_SIGNING_KEY usando default inseguro!\n"
            "Gere uma chave segura com: python -c \"import secrets; print(secrets.token_hex(64))\"\n"
            "Nunca use defaults em produção."
        )
    if len(key) < 32:
        raise ValueError(
            f"❌ LICENSE_SIGNING_KEY deve ter min 32 chars (tem {len(key)})\n"
            "Gere com: python -c \"import secrets; print(secrets.token_hex(64))\""
        )


# Validar secrets no import (fail-fast em produção)
_validate_license_signing_key()
LICENSE_SIGNING_KEY = settings.LICENSE_SIGNING_KEY
LICENSE_GRACE_PERIOD_HOURS = 24


def generate_license_key() -> str:
    """Gera uma chave de licença no formato FLORA-XXXX-XXXX-XXXX-XXXX."""
    parts = [secrets.token_hex(2).upper() for _ in range(4)]
    return f"FLORA-{'-'.join(parts)}"


def hash_license_key(key: str) -> str:
    """Gera hash SHA-256 da chave de licença."""
    return hashlib.sha256(key.encode()).hexdigest()


def sign_license(key: str) -> str:
    """Gera assinatura HMAC da chave de licença."""
    return hmac.new(
        LICENSE_SIGNING_KEY.encode(),
        key.encode(),
        hashlib.sha256,
    ).hexdigest()


def verify_license_signature(key: str, signature: str) -> bool:
    """Verifica se a assinatura da licença é válida."""
    expected = sign_license_key(key)
    return hmac.compare_digest(expected, signature)


def sign_license_key(key: str) -> str:
    """Alias para sign_license."""
    return sign_license(key)


def get_device_fingerprint() -> str:
    """Gera fingerprint do dispositivo atual."""
    components = [
        platform.node(),
        platform.machine(),
        platform.processor(),
        platform.system(),
    ]
    data = "|".join(components)
    return hashlib.sha256(data.encode()).hexdigest()[:16]


class LicenseManager:
    """Gerenciador de licenças."""

    def __init__(self):
        self._cache: dict[str, dict] = {}  # Cache de validação

    async def create_license(
        self,
        db: AsyncSession,
        user_id: str,
        plan_id: str,
        days_valid: int = 30,
        created_by: Optional[str] = None,
    ) -> tuple[License, str]:
        """
        Cria uma nova licença para um usuário.
        Retorna (License, plain_key) - a chave em texto plano só é retornada uma vez.
        """
        # Verificar se o plano existe
        plan_result = await db.execute(select(Plan).where(Plan.id == plan_id))
        plan = plan_result.scalar_one_or_none()
        if not plan:
            raise ValueError(f"Plano {plan_id} não encontrado")

        # Criar subscription
        now = datetime.now(timezone.utc)
        subscription = Subscription(
            user_id=user_id,
            plan_id=plan_id,
            status="active",
            billing_cycle="monthly",
            current_period_start=now,
            current_period_end=now + timedelta(days=days_valid),
        )
        db.add(subscription)
        await db.flush()

        # Gerar licença
        plain_key = generate_license_key()
        key_hash = hash_license_key(plain_key)
        signature = sign_license(plain_key)

        license_obj = License(
            id=str(uuid.uuid4()),
            subscription_id=subscription.id,
            license_key=plain_key,  # Salvar a chave original (será mascarada depois)
            key_hash=key_hash,
            signature=signature,
            status="active",
            max_bots=plan.max_bots,
            max_messages_per_day=plan.max_messages_per_day,
            features=plan.features,
            expires_at=now + timedelta(days=days_valid),
            created_by=created_by,
        )
        db.add(license_obj)
        await db.flush()

        logger.info(f"Licença criada: {plain_key[:12]}... para usuário {user_id}, plano {plan.name}")
        return license_obj, plain_key

    async def validate_license(
        self,
        db: AsyncSession,
        key: str,
        device_fingerprint: Optional[str] = None,
    ) -> dict:
        """
        Valida uma licença.
        Retorna dict com validade, motivo, plano, features, etc.
        """
        # Verificar formato
        if not re.match(r"^FLORA-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}$", key):
            return {
                "valid": False,
                "reason": "invalid_format",
                "message": "Formato de licença inválido.",
            }

        # Verificar cache
        cache_key = hash_license_key(key)
        cached = self._cache.get(cache_key)
        if cached and cached["expires"] > datetime.now(timezone.utc):
            return cached["result"]

        # Buscar no banco
        key_hash = hash_license_key(key)
        result = await db.execute(
            select(License).where(License.key_hash == key_hash)
        )
        lic = result.scalar_one_or_none()

        if not lic:
            return {
                "valid": False,
                "reason": "not_found",
                "message": "Licença não encontrada.",
            }

        # Verificar assinatura
        if not verify_license_signature(key, lic.signature):
            return {
                "valid": False,
                "reason": "invalid_signature",
                "message": "Assinatura da licença inválida.",
            }

        # Verificar status
        if lic.status == "revoked":
            return {
                "valid": False,
                "reason": "revoked",
                "message": "Esta licença foi revogada.",
            }

        if lic.status == "suspended":
            return {
                "valid": False,
                "reason": "suspended",
                "message": "Esta licença está suspensa.",
            }

        # Verificar expiração
        now = datetime.now(timezone.utc)
        if lic.expires_at and lic.expires_at < now:
            # Verificar grace period
            grace_end = lic.expires_at + timedelta(hours=LICENSE_GRACE_PERIOD_HOURS)
            if now > grace_end:
                lic.status = "expired"
                await db.flush()
                return {
                    "valid": False,
                    "reason": "expired",
                    "message": "Licença expirada. Renove para continuar usando.",
                    "expired_at": lic.expires_at.isoformat(),
                }
            else:
                days_left = (grace_end - now).days
                return {
                    "valid": True,
                    "reason": "grace_period",
                    "message": f"Licença em período de graça. Restam {days_left} dias.",
                    "grace_period": True,
                    "grace_ends_at": grace_end.isoformat(),
                }

        # Buscar plano
        plan_result = await db.execute(select(Plan).where(Plan.id == lic.subscription.plan_id))
        plan = plan_result.scalar_one_or_none()

        # Calcular dias restantes
        days_remaining = None
        if lic.expires_at:
            days_remaining = max(0, (lic.expires_at - now).days)

        result = {
            "valid": True,
            "reason": "active",
            "message": "Licença válida.",
            "license_id": lic.id,
            "plan": {
                "id": plan.id if plan else None,
                "name": plan.name if plan else "Desconhecido",
                "features": lic.features or {},
            },
            "expires_at": lic.expires_at.isoformat() if lic.expires_at else None,
            "days_remaining": days_remaining,
            "features": lic.features or {},
            "max_bots": lic.max_bots,
            "max_messages_per_day": lic.max_messages_per_day,
        }

        # Cache por 5 minutos
        self._cache[cache_key] = {
            "result": result,
            "expires": now + timedelta(minutes=5),
        }

        return result

    async def activate_license(
        self,
        db: AsyncSession,
        key: str,
        user_id: str,
        device_fingerprint: Optional[str] = None,
    ) -> dict:
        """Ativa uma licença para um usuário."""
        validation = await self.validate_license(db, key, device_fingerprint)
        if not validation["valid"]:
            return validation

        key_hash = hash_license_key(key)
        result = await db.execute(
            select(License).where(License.key_hash == key_hash)
        )
        lic = result.scalar_one_or_none()

        if lic.activated_at:
            return {
                "valid": False,
                "reason": "already_activated",
                "message": "Licença já está ativada.",
            }

        lic.activated_at = datetime.now(timezone.utc)
        lic.device_fingerprint = device_fingerprint
        await db.flush()

        logger.info(f"Licença ativada: {key[:12]}... para usuário {user_id}")
        return {
            "valid": True,
            "message": "Licença ativada com sucesso!",
            "license_id": lic.id,
            "plan": validation["plan"],
            "expires_at": lic.expires_at.isoformat() if lic.expires_at else None,
        }

    async def revoke_license(self, db: AsyncSession, license_id: str, reason: str = "") -> bool:
        """Revoga uma licença."""
        result = await db.execute(select(License).where(License.id == license_id))
        lic = result.scalar_one_or_none()

        if not lic:
            return False

        lic.status = "revoked"
        lic.revoked_at = datetime.now(timezone.utc)
        lic.revoked_reason = reason
        await db.flush()

        # Limpar cache
        for cache_key in list(self._cache.keys()):
            if self._cache[cache_key].get("result", {}).get("license_id") == license_id:
                del self._cache[cache_key]

        logger.info(f"Licença revogada: {license_id}. Motivo: {reason}")
        return True

    async def extend_license(
        self, db: AsyncSession, license_id: str, days: int
    ) -> Optional[License]:
        """Estende a validade de uma licença."""
        result = await db.execute(select(License).where(License.id == license_id))
        lic = result.scalar_one_or_none()

        if not lic:
            return None

        if lic.expires_at and lic.expires_at > datetime.now(timezone.utc):
            lic.expires_at += timedelta(days=days)
        else:
            lic.expires_at = datetime.now(timezone.utc) + timedelta(days=days)
            lic.status = "active"

        await db.flush()
        logger.info(f"Licença estendida: {license_id} por {days} dias")
        return lic

    async def get_user_licenses(self, db: AsyncSession, user_id: str) -> list[dict]:
        """Retorna todas as licenças de um usuário."""
        result = await db.execute(
            select(License)
            .join(Subscription)
            .where(Subscription.user_id == user_id)
            .order_by(License.created_at.desc())
        )
        licenses = result.scalars().all()

        output = []
        for lic in licenses:
            plan_result = await db.execute(select(Plan).where(Plan.id == lic.subscription.plan_id))
            plan = plan_result.scalar_one_or_none()

            days_remaining = None
            if lic.expires_at:
                days_remaining = max(0, (lic.expires_at - datetime.now(timezone.utc)).days)

            output.append({
                "id": lic.id,
                "license_key": f"{lic.license_key[:8]}...{lic.license_key[-4:]}",
                "status": lic.status,
                "plan_name": plan.name if plan else "Desconhecido",
                "expires_at": lic.expires_at.isoformat() if lic.expires_at else None,
                "days_remaining": days_remaining,
                "is_active": lic.status == "active" and (
                    not lic.expires_at or lic.expires_at > datetime.now(timezone.utc)
                ),
                "created_at": lic.created_at.isoformat() if lic.created_at else None,
            })

        return output

    async def check_feature_access(
        self, db: AsyncSession, license_id: str, feature: str
    ) -> bool:
        """Verifica se uma licença tem acesso a uma feature específica."""
        result = await db.execute(select(License).where(License.id == license_id))
        lic = result.scalar_one_or_none()

        if not lic or lic.status != "active":
            return False

        if lic.expires_at and lic.expires_at < datetime.now(timezone.utc):
            return False

        features = lic.features or {}
        return features.get(feature, False)


# Singleton
license_manager = LicenseManager()
