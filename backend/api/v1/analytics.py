"""Analytics Endpoints - API para métricas e relatórios."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user, get_current_admin, get_db

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/dashboard")
async def get_dashboard(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Dashboard principal com métricas gerais."""
    from backend.models.bot import Bot
    from backend.models.message import Message
    from backend.models.whatsapp_session import WhatsAppSession
    from datetime import datetime, timezone, timedelta

    # Total de bots do usuário
    bots_result = await db.execute(
        select(func.count(Bot.id)).where(Bot.owner_id == current_user.id)
    )
    total_bots = bots_result.scalar()

    # Bots ativos
    active_bots_result = await db.execute(
        select(func.count(Bot.id)).where(
            Bot.owner_id == current_user.id, Bot.is_active == True
        )
    )
    active_bots = active_bots_result.scalar()

    # Total de mensagens
    messages_result = await db.execute(
        select(func.count(Message.id)).where(Message.owner_id == current_user.id)
    )
    total_messages = messages_result.scalar()

    # Mensagens hoje
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    today_messages_result = await db.execute(
        select(func.count(Message.id)).where(
            Message.owner_id == current_user.id,
            Message.created_at >= today,
        )
    )
    messages_today = today_messages_result.scalar()

    # Sessões WhatsApp conectadas
    ws_result = await db.execute(
        select(func.count(WhatsAppSession.id)).where(
            WhatsAppSession.owner_id == current_user.id,
            WhatsAppSession.status == "connected",
        )
    )
    connected_sessions = ws_result.scalar()

    return {
        "total_bots": total_bots,
        "active_bots": active_bots,
        "total_messages": total_messages,
        "messages_today": messages_today,
        "connected_whatsapp_sessions": connected_sessions,
    }


@router.get("/bots/{bot_id}")
async def get_bot_analytics(
    bot_id: str,
    days: int = Query(30, ge=1, le=365),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Analytics detalhado de um bot."""
    from backend.models.message import Message
    from datetime import datetime, timezone, timedelta

    since = datetime.now(timezone.utc) - timedelta(days=days)

    # Total de mensagens no período
    total_result = await db.execute(
        select(func.count(Message.id)).where(
            Message.bot_id == bot_id, Message.created_at >= since
        )
    )
    total_messages = total_result.scalar()

    # Mensagens por dia
    daily_result = await db.execute(
        select(
            func.date(Message.created_at).label("date"),
            func.count(Message.id).label("count"),
        )
        .where(Message.bot_id == bot_id, Message.created_at >= since)
        .group_by(func.date(Message.created_at))
        .order_by(func.date(Message.created_at))
    )
    daily_messages = [
        {"date": str(row.date), "count": row.count} for row in daily_result.all()
    ]

    # Conversas únicas
    conversations_result = await db.execute(
        select(func.count(func.distinct(Message.sender))).where(
            Message.bot_id == bot_id, Message.created_at >= since
        )
    )
    unique_conversations = conversations_result.scalar()

    return {
        "bot_id": bot_id,
        "period_days": days,
        "total_messages": total_messages,
        "unique_conversations": unique_conversations,
        "daily_messages": daily_messages,
    }


@router.get("/messages")
async def get_message_stats(
    days: int = Query(30, ge=1, le=365),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Estatísticas de mensagens."""
    from backend.models.message import Message
    from datetime import datetime, timezone, timedelta

    since = datetime.now(timezone.utc) - timedelta(days=days)

    result = await db.execute(
        select(
            func.count(Message.id).label("total"),
            func.count(func.distinct(Message.sender)).label("unique_senders"),
            func.count(func.distinct(Message.bot_id)).label("active_bots"),
        ).where(
            Message.owner_id == current_user.id,
            Message.created_at >= since,
        )
    )
    stats = result.one()

    return {
        "period_days": days,
        "total_messages": stats.total,
        "unique_senders": stats.unique_senders,
        "active_bots": stats.active_bots,
    }


@router.get("/users")
async def get_user_stats(
    current_user=Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Estatísticas de usuários (admin only)."""
    from backend.models.user import User
    from datetime import datetime, timezone, timedelta

    total_result = await db.execute(select(func.count(User.id)))
    total_users = total_result.scalar()

    active_result = await db.execute(
        select(func.count(User.id)).where(User.is_active == True)
    )
    active_users = active_result.scalar()

    # Novos usuários esta semana
    week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    new_result = await db.execute(
        select(func.count(User.id)).where(User.created_at >= week_ago)
    )
    new_users_week = new_result.scalar()

    return {
        "total_users": total_users,
        "active_users": active_users,
        "new_users_this_week": new_users_week,
    }


@router.get("/revenue")
async def get_revenue_stats(
    days: int = Query(30, ge=1, le=365),
    current_user=Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Estatísticas de receita (admin only)."""
    from backend.models.payment import Payment
    from datetime import datetime, timezone, timedelta

    since = datetime.now(timezone.utc) - timedelta(days=days)

    result = await db.execute(
        select(
            func.count(Payment.id).label("total_payments"),
            func.sum(Payment.amount).label("total_revenue"),
            func.avg(Payment.amount).label("avg_payment"),
        ).where(
            Payment.status == "completed",
            Payment.created_at >= since,
        )
    )
    stats = result.one()

    return {
        "period_days": days,
        "total_payments": stats.total_payments or 0,
        "total_revenue": round(float(stats.total_revenue or 0), 2),
        "average_payment": round(float(stats.avg_payment or 0), 2),
    }


@router.get("/llm-usage")
async def get_llm_usage_stats(
    days: int = Query(30, ge=1, le=365),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Estatísticas de uso de LLM."""
    from backend.models.llm_usage import LLMUsage
    from datetime import datetime, timezone, timedelta

    since = datetime.now(timezone.utc) - timedelta(days=days)

    result = await db.execute(
        select(
            func.count(LLMUsage.id).label("total_requests"),
            func.sum(LLMUsage.total_tokens).label("total_tokens"),
            func.avg(LLMUsage.response_time_ms).label("avg_response_time"),
            func.sum(LLMUsage.cost).label("total_cost"),
        ).where(LLMUsage.created_at >= since)
    )
    stats = result.one()

    return {
        "period_days": days,
        "total_requests": stats.total_requests or 0,
        "total_tokens": int(stats.total_tokens or 0),
        "avg_response_time_ms": round(float(stats.avg_response_time or 0), 2),
        "total_cost": round(float(stats.total_cost or 0), 4),
    }


@router.get("/export")
async def export_analytics(
    format: str = Query("json", regex="^(json|csv)$"),
    days: int = Query(30, ge=1, le=365),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Exporta dados de analytics."""
    return {
        "format": format,
        "period_days": days,
        "message": "Exportação iniciada. O arquivo será enviado por notificação.",
    }
