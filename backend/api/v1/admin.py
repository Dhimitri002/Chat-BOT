"""Admin Endpoints - API para administradores da plataforma Flora."""
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_admin, get_db
from backend.models.user import User
from backend.models.bot import Bot
from backend.models.license import License
from backend.models.plan import Plan
from backend.models.message import Message
from backend.models.payment import Payment
from backend.models.llm_usage import LLMUsage
from backend.models.whatsapp_session import WhatsAppSession

router = APIRouter(prefix="/admin", tags=["admin"])


# ── Dashboard ──────────────────────────────────────────────────────────────

@router.get("/dashboard")
async def admin_dashboard(
    current_user=Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Dashboard administrativo com metricas globais."""

    # Users
    total_users_result = await db.execute(select(func.count(User.id)))
    total_users = total_users_result.scalar() or 0

    active_users_result = await db.execute(
        select(func.count(User.id)).where(User.is_active == True)
    )
    active_users = active_users_result.scalar() or 0

    # Bots
    total_bots_result = await db.execute(select(func.count(Bot.id)))
    total_bots = total_bots_result.scalar() or 0

    active_bots_result = await db.execute(
        select(func.count(Bot.id)).where(Bot.is_active == True)
    )
    active_bots = active_bots_result.scalar() or 0

    # Licenses
    total_licenses_result = await db.execute(select(func.count(License.id)))
    total_licenses = total_licenses_result.scalar() or 0

    active_licenses_result = await db.execute(
        select(func.count(License.id)).where(License.status == "active")
    )
    active_licenses = active_licenses_result.scalar() or 0

    now = datetime.now(timezone.utc)
    expiring_licenses_result = await db.execute(
        select(func.count(License.id)).where(
            License.status == "active",
            License.expires_at <= now,
        )
    )
    expiring_licenses = expiring_licenses_result.scalar() or 0

    # Revenue
    total_revenue_result = await db.execute(
        select(func.sum(Payment.amount)).where(Payment.status == "completed")
    )
    total_revenue = float(total_revenue_result.scalar() or 0)

    # Messages today
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    messages_today_result = await db.execute(
        select(func.count(Message.id)).where(Message.created_at >= today_start)
    )
    messages_today = messages_today_result.scalar() or 0

    # LLM usage today
    llm_today_result = await db.execute(
        select(func.sum(LLMUsage.total_tokens)).where(LLMUsage.created_at >= today_start)
    )
    llm_tokens_today = llm_today_result.scalar() or 0

    llm_cost_result = await db.execute(
        select(func.sum(LLMUsage.cost)).where(LLMUsage.created_at >= today_start)
    )
    llm_cost_today = float(llm_cost_result.scalar() or 0)

    # New users today
    new_users_today_result = await db.execute(
        select(func.count(User.id)).where(User.created_at >= today_start)
    )
    new_users_today = new_users_today_result.scalar() or 0

    return {
        "users": {
            "total": total_users,
            "active": active_users,
            "new_today": new_users_today,
        },
        "bots": {
            "total": total_bots,
            "active": active_bots,
        },
        "licenses": {
            "total": total_licenses,
            "active": active_licenses,
            "expiring": expiring_licenses,
        },
        "revenue": {
            "total": total_revenue,
        },
        "messages": {
            "today": messages_today,
        },
        "llm": {
            "tokens_today": llm_tokens_today,
            "cost_today": llm_cost_today,
        },
    }


# ── User Management ────────────────────────────────────────────────────────

@router.get("/users")
async def admin_list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    current_user=Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Lista todos os usuarios (admin)."""
    query = select(User)

    if search:
        query = query.where(
            (User.name.ilike(f"%{search}%")) | (User.email.ilike(f"%{search}%"))
        )
    if is_active is not None:
        query = query.where(User.is_active == is_active)

    query = query.order_by(User.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    users = result.scalars().all()

    return {
        "users": [
            {
                "id": u.id,
                "name": u.name,
                "email": u.email,
                "role": u.role,
                "is_active": u.is_active,
                "last_login": u.last_login.isoformat() if u.last_login else None,
                "created_at": u.created_at.isoformat() if u.created_at else None,
            }
            for u in users
        ],
        "page": page,
        "page_size": page_size,
    }


@router.get("/users/{user_id}")
async def admin_get_user(
    user_id: str,
    current_user=Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Obtem detalhes de um usuario (admin)."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active,
        "is_2fa_enabled": user.is_2fa_enabled,
        "avatar_url": user.avatar_url,
        "last_login": user.last_login.isoformat() if user.last_login else None,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "updated_at": user.updated_at.isoformat() if user.updated_at else None,
    }


class AdminUserUpdateRequest(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


@router.patch("/users/{user_id}")
async def admin_update_user(
    user_id: str,
    data: AdminUserUpdateRequest,
    current_user=Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Atualiza um usuario (admin)."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    await db.commit()
    await db.refresh(user)

    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active,
    }


@router.delete("/users/{user_id}")
async def admin_delete_user(
    user_id: str,
    current_user=Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Deleta um usuario (admin)."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await db.delete(user)
    await db.commit()

    return {"message": "User deleted successfully"}


# ── Bot Management ─────────────────────────────────────────────────────────

@router.get("/bots")
async def admin_list_bots(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    is_active: Optional[bool] = None,
    current_user=Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Lista todos os bots (admin)."""
    query = select(Bot)

    if is_active is not None:
        query = query.where(Bot.is_active == is_active)

    query = query.order_by(Bot.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    bots = result.scalars().all()

    return {
        "bots": [
            {
                "id": b.id,
                "name": b.name,
                "owner_id": b.owner_id,
                "license_id": b.license_id,
                "is_active": b.is_active,
                "is_connected": b.is_connected,
                "created_at": b.created_at.isoformat() if b.created_at else None,
            }
            for b in bots
        ],
        "page": page,
        "page_size": page_size,
    }


@router.get("/bots/{bot_id}")
async def admin_get_bot(
    bot_id: str,
    current_user=Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Obtem detalhes de um bot (admin)."""
    result = await db.execute(select(Bot).where(Bot.id == bot_id))
    bot = result.scalar_one_or_none()

    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")

    return {
        "id": bot.id,
        "name": bot.name,
        "owner_id": bot.owner_id,
        "license_id": bot.license_id,
        "prompt": bot.prompt,
        "personality": bot.personality,
        "tone": bot.tone,
        "language": bot.language,
        "is_active": bot.is_active,
        "is_connected": bot.is_connected,
        "preferred_llm": bot.preferred_llm,
        "temperature": bot.temperature,
        "max_tokens": bot.max_tokens,
        "version": bot.version,
        "created_at": bot.created_at.isoformat() if bot.created_at else None,
        "updated_at": bot.updated_at.isoformat() if bot.updated_at else None,
    }


@router.patch("/bots/{bot_id}")
async def admin_update_bot(
    bot_id: str,
    data: AdminUserUpdateRequest,
    current_user=Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Atualiza um bot (admin)."""
    result = await db.execute(select(Bot).where(Bot.id == bot_id))
    bot = result.scalar_one_or_none()

    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(bot, field):
            setattr(bot, field, value)

    await db.commit()
    await db.refresh(bot)

    return {"id": bot.id, "name": bot.name, "is_active": bot.is_active}


@router.delete("/bots/{bot_id}")
async def admin_delete_bot(
    bot_id: str,
    current_user=Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Deleta um bot (admin)."""
    result = await db.execute(select(Bot).where(Bot.id == bot_id))
    bot = result.scalar_one_or_none()

    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")

    await db.delete(bot)
    await db.commit()

    return {"message": "Bot deleted successfully"}


# ── License Management ─────────────────────────────────────────────────────

@router.get("/licenses")
async def admin_list_licenses(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    current_user=Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Lista todas as licencas (admin)."""
    query = select(License)

    if status:
        query = query.where(License.status == status)

    query = query.order_by(License.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    licenses = result.scalars().all()

    return {
        "licenses": [
            {
                "id": lic.id,
                "license_key": lic.license_key,
                "user_id": lic.user_id,
                "plan_id": lic.plan_id,
                "status": lic.status,
                "is_active": lic.is_active,
                "expires_at": lic.expires_at.isoformat() if lic.expires_at else None,
                "created_at": lic.created_at.isoformat() if lic.created_at else None,
            }
            for lic in licenses
        ],
        "page": page,
        "page_size": page_size,
    }


@router.get("/licenses/{license_id}")
async def admin_get_license(
    license_id: str,
    current_user=Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Obtem detalhes de uma licenca (admin)."""
    result = await db.execute(select(License).where(License.id == license_id))
    lic = result.scalar_one_or_none()

    if not lic:
        raise HTTPException(status_code=404, detail="License not found")

    return {
        "id": lic.id,
        "license_key": lic.license_key,
        "key_hash": lic.key_hash,
        "user_id": lic.user_id,
        "plan_id": lic.plan_id,
        "status": lic.status,
        "is_active": lic.is_active,
        "starts_at": lic.starts_at.isoformat() if lic.starts_at else None,
        "expires_at": lic.expires_at.isoformat() if lic.expires_at else None,
        "max_devices": lic.max_devices,
        "created_at": lic.created_at.isoformat() if lic.created_at else None,
        "updated_at": lic.updated_at.isoformat() if lic.updated_at else None,
    }


# ── Plan Management ────────────────────────────────────────────────────────

@router.get("/plans")
async def admin_list_plans(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user=Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Lista todos os planos (admin)."""
    query = select(Plan).order_by(Plan.display_order.asc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    plans = result.scalars().all()

    return {
        "plans": [
            {
                "id": p.id,
                "name": p.name,
                "slug": p.slug,
                "price_monthly": p.price_monthly,
                "price_yearly": p.price_yearly,
                "is_active": p.is_active,
                "is_public": p.is_public,
                "display_order": p.display_order,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in plans
        ],
        "page": page,
        "page_size": page_size,
    }


# ── WhatsApp Sessions ──────────────────────────────────────────────────────

@router.get("/whatsapp/sessions")
async def admin_list_whatsapp_sessions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user=Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Lista todas as sessoes WhatsApp (admin)."""
    query = select(WhatsAppSession).order_by(WhatsAppSession.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    sessions = result.scalars().all()

    return {
        "sessions": [
            {
                "id": s.id,
                "owner_id": s.owner_id,
                "phone_number": s.phone_number,
                "status": s.status,
                "created_at": s.created_at.isoformat() if s.created_at else None,
            }
            for s in sessions
        ],
        "page": page,
        "page_size": page_size,
    }


# ── System Stats ───────────────────────────────────────────────────────────

@router.get("/stats")
async def admin_system_stats(
    current_user=Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Estatisticas gerais do sistema."""
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # Messages stats
    total_messages_result = await db.execute(select(func.count(Message.id)))
    total_messages = total_messages_result.scalar() or 0

    today_messages_result = await db.execute(
        select(func.count(Message.id)).where(Message.created_at >= today_start)
    )
    today_messages = today_messages_result.scalar() or 0

    # LLM stats
    llm_total_result = await db.execute(select(func.sum(LLMUsage.total_tokens)))
    llm_total_tokens = llm_total_result.scalar() or 0

    llm_cost_result = await db.execute(select(func.sum(LLMUsage.cost)))
    llm_total_cost = float(llm_cost_result.scalar() or 0)

    # Connected WhatsApp sessions
    connected_ws_result = await db.execute(
        select(func.count(WhatsAppSession.id)).where(
            WhatsAppSession.status == "connected"
        )
    )
    connected_sessions = connected_ws_result.scalar() or 0

    return {
        "messages": {
            "total": total_messages,
            "today": today_messages,
        },
        "llm": {
            "total_tokens": llm_total_tokens,
            "total_cost": llm_total_cost,
        },
        "whatsapp": {
            "connected_sessions": connected_sessions,
        },
    }
