"""License Service"""
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger

from backend.models.license import License
from backend.models.subscription import Subscription
from backend.models.plan import Plan
from backend.core.security import generate_license_key, hash_license_key, generate_hmac


LICENSE_SECRET = "flora-license-signing-secret-change-in-production"


async def create_license(
    db: AsyncSession,
    user_id: str,
    plan_id: str,
    days_valid: int = 30,
) -> License:
    # Create subscription
    now = datetime.now(timezone.utc)
    sub = Subscription(
        user_id=user_id,
        plan_id=plan_id,
        status="active",
        billing_cycle="monthly",
        current_period_start=now,
        current_period_end=now + timedelta(days=days_valid),
    )
    db.add(sub)
    await db.flush()

    # Generate license
    key = generate_license_key()
    key_hash = hash_license_key(key)
    signature = generate_hmac(key, LICENSE_SECRET)

    license_obj = License(
        subscription_id=sub.id,
        license_key=key,
        key_hash=key_hash,
        signature=signature,
        status="active",
        expires_at=now + timedelta(days=days_valid),
    )
    db.add(license_obj)
    await db.flush()
    logger.info(f"License created: {key} for user {user_id}")
    return license_obj


async def validate_license(db: AsyncSession, key: str, device_fingerprint: str = None) -> dict:
    key_hash = hash_license_key(key)

    result = await db.execute(
        select(License).where(License.key_hash == key_hash)
    )
    lic = result.scalar_one_or_none()

    if not lic:
        return {"valid": False, "reason": "not_found", "message": "Licença não encontrada."}

    # Verify signature
    expected_sig = generate_hmac(key, LICENSE_SECRET)
    if lic.signature != expected_sig:
        return {"valid": False, "reason": "invalid_signature", "message": "Assinatura inválida."}

    if lic.status != "active":
        return {"valid": False, "reason": f"license_{lic.status}", "message": f"Licença {lic.status}."}

    if lic.expires_at < datetime.now(timezone.utc):
        return {"valid": False, "reason": "expired", "message": "Licença expirada."}

    # Device check
    if lic.device_fingerprint and device_fingerprint and lic.device_fingerprint != device_fingerprint:
        return {"valid": False, "reason": "device_mismatch", "message": "Dispositivo não autorizado."}

    # Rate limit
    if lic.validation_count >= lic.max_validations:
        return {"valid": False, "reason": "validation_limit", "message": "Limite de validações excedido."}

    # Update validation
    lic.validation_count += 1
    lic.last_validated_at = datetime.now(timezone.utc)
    if device_fingerprint and not lic.device_fingerprint:
        lic.device_fingerprint = device_fingerprint

    # Get plan info
    sub_result = await db.execute(
        select(Subscription).where(Subscription.id == lic.subscription_id)
    )
    sub = sub_result.scalar_one_or_none()

    plan_result = await db.execute(
        select(Plan).where(Plan.id == sub.plan_id)
    )
    plan = plan_result.scalar_one_or_none()

    days_remaining = (lic.expires_at - datetime.now(timezone.utc)).days

    return {
        "valid": True,
        "plan": {
            "id": plan.id,
            "name": plan.name,
            "slug": plan.slug,
            "features": {
                "has_llm": plan.has_llm,
                "llm_provider": plan.llm_provider,
                "llm_model": plan.llm_model,
                "has_flora": plan.has_flora,
                "has_media": plan.has_media,
                "has_pdf": plan.has_pdf,
                "has_image": plan.has_image,
                "has_webhooks": plan.has_webhooks,
                "has_analytics": plan.has_analytics,
                "has_custom_commands": plan.has_custom_commands,
                "has_automations": plan.has_automations,
                "max_messages_month": plan.max_messages_month,
                "max_commands": plan.max_commands,
                "max_memory_items": plan.max_memory_items,
            },
        },
        "expires_at": lic.expires_at,
        "days_remaining": max(0, days_remaining),
    }
