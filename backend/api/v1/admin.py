"""Admin Endpoints — API administrativa da plataforma."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_admin, get_db
from backend.models.bot import Bot
from backend.models.message import Message
from backend.models.user import User
from backend.models.license import License
from backend.models.subscription import Subscription
from backend.services.license_service import LicenseService

router = APIRouter()


class UpdateUserRequest(BaseModel):
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    role: Optional[str] = None


class BroadcastRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=5000)
    target: str = Field(default="all")


# ─── Dashboard ────────────────────────────────────────────

@router.get("/dashboard")
async def admin_dashboard(
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Dashboard administrativo com métricas globais."""
    # Total de usuários
    users_count = (await db.execute(select(func.count()).select_from(User))).scalar() or 0

    # Total de bots
    bots_count = (await db.execute(select(func.count()).select_from(Bot))).scalar() or 0

    # Bots ativos
    active_bots = (await db.execute(
        select(func.count()).where(Bot.is_active == True)
    )).scalar() or 0

    # Total de mensagens
    messages_count = (await db.execute(select(func.count()).select_from(Message))).scalar() or 0

    # Mensagens hoje
    from datetime import datetime, timedelta
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    messages_today = (await db.execute(
        select(func.count()).where(Message.created_at >= today)
    )).scalar() or 0

    # Licenças ativas
    active_licenses = (await db.execute(
        select(func.count()).where(License.status == "active")
    )).scalar() or 0

    # Assinaturas ativas
    active_subs = (await db.execute(
        select(func.count()).where(Subscription.status == "active")
    )).scalar() or 0

    # Usuários novos hoje
    new_users_today = (await db.execute(
        select(func.count()).where(User.created_at >= today)
    )).scalar() or 0

    return {
        "users": {
            "total": users_count,
            "new_today": new_users_today,
        },
        "bots": {
            "total": bots_count,
            "active": active_bots,
        },
        "messages": {
            "total": messages_count,
            "today": messages_today,
        },
        "licenses": {
            "active": active_licenses,
        },
        "subscriptions": {
            "active": active_subs,
        },
    }


# ─── Gestão de Usuários ───────────────────────────────────

@router.get("/users")
async def admin_list_users(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Lista todos os usuários (admin)."""
    query = select(User)

    if search:
        query = query.where(
            User.email.contains(search) | User.full_name.contains(search)
        )

    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar() or 0

    offset = (page - 1) * per_page
    result = await db.execute(
        query.order_by(User.created_at.desc()).offset(offset).limit(per_page)
    )
    users = result.scalars().all()

    return {
        "users": [
            {
                "id": str(u.id),
                "email": u.email,
                "full_name": u.full_name,
                "role": u.role,
                "is_active": u.is_active,
                "created_at": u.created_at.isoformat() if u.created_at else None,
            }
            for u in users
        ],
        "total": total,
        "page": page,
        "per_page": per_page,
    }


@router.get("/users/{user_id}")
async def admin_get_user(
    user_id: str,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Obtém detalhes de um usuário."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    # Contar bots do usuário
    bots_count = (await db.execute(
        select(func.count()).where(Bot.user_id == user_id)
    )).scalar() or 0

    return {
        "id": str(user.id),
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "is_active": user.is_active,
        "is_verified": user.is_verified,
        "bots_count": bots_count,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "last_login": user.last_login.isoformat() if user.last_login else None,
    }


@router.put("/users/{user_id}/role")
async def admin_update_user_role(
    user_id: str,
    role: str = Query(..., regex="^(user|admin)$"),
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Atualiza role de um usuário."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    user.role = role
    await db.commit()
    return {"message": f"Role atualizada para '{role}'"}


@router.put("/users/{user_id}/status")
async def admin_update_user_status(
    user_id: str,
    is_active: bool = Query(...),
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Ativa/desativa um usuário."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    user.is_active = is_active
    await db.commit()
    return {"message": f"Usuário {'ativado' if is_active else 'desativado'}"}


# ─── Gestão de Bots ───────────────────────────────────────

@router.get("/bots")
async def admin_list_bots(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Lista todos os bots (admin)."""
    count_result = await db.execute(select(func.count()).select_from(Bot))
    total = count_result.scalar() or 0

    offset = (page - 1) * per_page
    result = await db.execute(
        select(Bot).order_by(Bot.created_at.desc()).offset(offset).limit(per_page)
    )
    bots = result.scalars().all()

    return {
        "bots": [
            {
                "id": str(b.id),
                "name": b.name,
                "user_id": str(b.user_id),
                "is_active": b.is_active,
                "created_at": b.created_at.isoformat() if b.created_at else None,
            }
            for b in bots
        ],
        "total": total,
    }


# ─── Sistema ──────────────────────────────────────────────

@router.get("/system/events")
async def admin_system_events(
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Lista eventos do sistema."""
    from backend.models.system_event import SystemEvent

    result = await db.execute(
        select(SystemEvent)
        .order_by(SystemEvent.created_at.desc())
        .limit(limit)
    )
    events = result.scalars().all()

    return {
        "events": [
            {
                "id": str(e.id),
                "event_type": e.event_type,
                "severity": e.severity,
                "message": e.message,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in events
        ],
    }


@router.post("/system/broadcast")
async def admin_broadcast(
    request: BroadcastRequest,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Envia notificação em massa."""
    from backend.models.notification import Notification

    # Buscar usuários alvo
    query = select(User.id).where(User.is_active == True)
    if request.target == "premium":
        # Usuários com licenças premium
        query = query.join(License, User.id == License.user_id).where(
            License.status == "active"
        )

    result = await db.execute(query)
    user_ids = [str(u[0]) for u in result.all()]

    # Criar notificações
    for uid in user_ids:
        notif = Notification(
            user_id=uid,
            title="Aviso da Administração",
            body=request.message,
            type="broadcast",
            is_read=False,
        )
        db.add(notif)

    await db.commit()

    return {"message": f"Notificação enviada para {len(user_ids)} usuários"}


# ─── Analytics ────────────────────────────────────────────

@router.get("/analytics/overview")
async def admin_analytics_overview(
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Analytics global da plataforma."""
    from datetime import datetime, timedelta

    # Mensagens por dia (últimos 7 dias)
    days = []
    for i in range(7):
        day = datetime.utcnow() - timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)

        count = (await db.execute(
            select(func.count())
            .where(Message.created_at >= day_start)
            .where(Message.created_at < day_end)
        )).scalar() or 0

        days.append({
            "date": day_start.strftime("%Y-%m-%d"),
            "messages": count,
        })

    return {
        "messages_by_day": list(reversed(days)),
        "total_users": (await db.execute(select(func.count()).select_from(User))).scalar() or 0,
        "total_bots": (await db.execute(select(func.count()).select_from(Bot))).scalar() or 0,
        "total_messages": (await db.execute(select(func.count()).select_from(Message))).scalar() or 0,
    }


# ─── Suporte ──────────────────────────────────────────────

@router.get("/support/tickets")
async def admin_list_tickets(
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Lista tickets de suporte."""
    from backend.models.support_ticket import SupportTicket

    query = select(SupportTicket)
    if status:
        query = query.where(SupportTicket.status == status)

    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar() or 0

    offset = (page - 1) * per_page
    result = await db.execute(
        query.order_by(SupportTicket.created_at.desc()).offset(offset).limit(per_page)
    )
    tickets = result.scalars().all()

    return {
        "tickets": [
            {
                "id": str(t.id),
                "subject": t.subject,
                "status": t.status,
                "priority": t.priority,
                "user_id": str(t.user_id),
                "created_at": t.created_at.isoformat() if t.created_at else None,
            }
            for t in tickets
        ],
        "total": total,
    }


@router.put("/support/tickets/{ticket_id}")
async def admin_update_ticket(
    ticket_id: str,
    status: Optional[str] = None,
    assigned_to: Optional[str] = None,
    resolution: Optional[str] = None,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Atualiza ticket de suporte."""
    from backend.models.support_ticket import SupportTicket

    result = await db.execute(select(SupportTicket).where(SupportTicket.id == ticket_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket não encontrado")

    if status:
        ticket.status = status
    if assigned_to:
        ticket.assigned_to = assigned_to
    if resolution:
        ticket.resolution = resolution

    await db.commit()
    return {"message": "Ticket atualizado"}
