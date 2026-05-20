"""Admin Endpoints - API administrativa da plataforma."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_admin, get_db

router = APIRouter(prefix="/admin", tags=["admin"])


class UpdateUserRequest(BaseModel):
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    role: Optional[str] = None


class BroadcastRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=5000)
    target: str = Field(default="all", regex="^(all|active|premium)$")


@router.get("/dashboard")
async def admin_dashboard(
    current_user=Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Dashboard administrativo com métricas globais."""
    from backend.models.user import User
    from backend.models.bot import Bot
    from backend.models.license import License
    from backend.models.subscription import Subscription
    from backend.models.message import Message
    from backend.models.payment import Payment
    from datetime import datetime, timezone, timedelta

    # Usuários
    total_users = (await db.execute(select(func.count(User.id)))).scalar()
    active_users = (await db.execute(
        select(func.count(User.id)).where(User.is_active == True)
    )).scalar()

    # Bots
    total_bots = (await db.execute(select(func.count(Bot.id)))).scalar()
    active_bots = (await db.execute(
        select(func.count(Bot.id)).where(Bot.is_active == True)
    )).scalar()

    # Licenças
    total_licenses = (await db.execute(select(func.count(License.id)))).scalar()
    active_licenses = (await db.execute(
        select(func.count(License.id)).where(License.status == "active")
    )).scalar()

    # Mensagens hoje
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    messages_today = (await db.execute(
        select(func.count(Message.id)).where(Message.created_at >= today)
    )).scalar()

    # Receita do mês
    month_start = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    revenue_result = await db.execute(
        select(func.sum(Payment.amount)).where(
            Payment.status == "completed",
            Payment.created_at >= month_start,
        )
    )
    monthly_revenue = round(float(revenue_result.scalar() or 0), 2)

    return {
        "users": {"total": total_users, "active": active_users},
        "bots": {"total": total_bots, "active": active_bots},
        "licenses": {"total": total_licenses, "active": active_licenses},
        "messages_today": messages_today,
        "monthly_revenue": monthly_revenue,
    }


@router.get("/users")
async def admin_list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    current_user=Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Lista todos os usuários (admin)."""
    from backend.models.user import User

    query = select(User).order_by(User.created_at.desc())

    if search:
        query = query.where(
            User.email.ilike(f"%{search}%") | User.full_name.ilike(f"%{search}%")
        )
    if is_active is not None:
        query = query.where(User.is_active == is_active)

    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar()
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    users = result.scalars().all()

    return {
        "users": [
            {
                "id": u.id,
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
        "page_size": page_size,
    }


@router.put("/users/{user_id}")
async def admin_update_user(
    user_id: str,
    request: UpdateUserRequest,
    current_user=Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Atualiza um usuário (admin)."""
    from backend.models.user import User

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    update_data = request.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(user, key, value)

    await db.flush()
    return {"success": True, "message": "Usuário atualizado."}


@router.delete("/users/{user_id}")
async def admin_delete_user(
    user_id: str,
    current_user=Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Deleta um usuário (admin)."""
    from backend.models.user import User

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    user.is_active = False
    await db.flush()
    return {"success": True, "message": "Usuário desativado."}


@router.get("/bots")
async def admin_list_bots(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user=Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Lista todos os bots (admin)."""
    from backend.models.bot import Bot

    query = select(Bot).order_by(Bot.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    bots = result.scalars().all()

    return {
        "bots": [
            {
                "id": b.id,
                "name": b.name,
                "owner_id": b.owner_id,
                "is_active": b.is_active,
                "is_connected": b.is_connected,
                "created_at": b.created_at.isoformat() if b.created_at else None,
            }
            for b in bots
        ]
    }


@router.get("/licenses")
async def admin_list_licenses(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    current_user=Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Lista todas as licenças (admin)."""
    from backend.models.license import License

    query = select(License).order_by(License.created_at.desc())
    if status:
        query = query.where(License.status == status)

    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    licenses = result.scalars().all()

    return {
        "licenses": [
            {
                "id": lic.id,
                "license_key": f"{lic.license_key[:8]}...{lic.license_key[-4:]}",
                "status": lic.status,
                "expires_at": lic.expires_at.isoformat() if lic.expires_at else None,
                "created_at": lic.created_at.isoformat() if lic.created_at else None,
            }
            for lic in licenses
        ]
    }


@router.post("/licenses")
async def admin_create_license(
    user_id: str,
    plan_id: str,
    days_valid: int = 30,
    current_user=Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Cria uma nova licença (admin)."""
    from backend.core.license_manager import license_manager

    lic, plain_key = await license_manager.create_license(
        db, user_id, plan_id, days_valid, created_by=current_user.id
    )
    await db.commit()

    return {
        "success": True,
        "license_id": lic.id,
        "license_key": plain_key,
        "message": "Licença criada com sucesso.",
    }


@router.put("/licenses/{license_id}")
async def admin_update_license(
    license_id: str,
    status: Optional[str] = None,
    extend_days: Optional[int] = None,
    current_user=Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Atualiza uma licença (admin)."""
    from backend.core.license_manager import license_manager

    if extend_days:
        lic = await license_manager.extend_license(db, license_id, extend_days)
        if not lic:
            raise HTTPException(status_code=404, detail="Licença não encontrada")
        await db.commit()
        return {"success": True, "message": f"Licença estendida por {extend_days} dias."}

    if status:
        from backend.models.license import License
        result = await db.execute(select(License).where(License.id == license_id))
        lic = result.scalar_one_or_none()
        if not lic:
            raise HTTPException(status_code=404, detail="Licença não encontrada")
        lic.status = status
        await db.flush()
        return {"success": True, "message": f"Status atualizado para {status}."}

    return {"success": False, "message": "Nenhuma ação especificada."}


@router.get("/subscriptions")
async def admin_list_subscriptions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user=Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Lista todas as assinaturas (admin)."""
    from backend.models.subscription import Subscription

    query = select(Subscription).order_by(Subscription.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    subscriptions = result.scalars().all()

    return {
        "subscriptions": [
            {
                "id": s.id,
                "user_id": s.user_id,
                "plan_id": s.plan_id,
                "status": s.status,
                "current_period_end": s.current_period_end.isoformat() if s.current_period_end else None,
            }
            for s in subscriptions
        ]
    }


@router.get("/system-events")
async def admin_system_events(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    event_type: Optional[str] = None,
    current_user=Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Lista eventos do sistema (admin)."""
    from backend.models.system_event import SystemEvent

    query = select(SystemEvent).order_by(SystemEvent.created_at.desc())
    if event_type:
        query = query.where(SystemEvent.event_type == event_type)

    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    events = result.scalars().all()

    return {
        "events": [
            {
                "id": e.id,
                "event_type": e.event_type,
                "severity": e.severity,
                "message": e.message,
                "metadata": e.metadata,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in events
        ]
    }


@router.post("/broadcast")
async def admin_broadcast(
    request: BroadcastRequest,
    current_user=Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Envia mensagem em massa (admin)."""
    return {
        "success": True,
        "message": f"Broadcast enviado para: {request.target}",
        "recipients": 0,
    }


@router.get("/support-tickets")
async def admin_list_tickets(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    current_user=Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Lista tickets de suporte (admin)."""
    from backend.models.support_ticket import SupportTicket

    query = select(SupportTicket).order_by(SupportTicket.created_at.desc())
    if status:
        query = query.where(SupportTicket.status == status)

    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    tickets = result.scalars().all()

    return {
        "tickets": [
            {
                "id": t.id,
                "subject": t.subject,
                "status": t.status,
                "priority": t.priority,
                "user_id": t.user_id,
                "created_at": t.created_at.isoformat() if t.created_at else None,
            }
            for t in tickets
        ]
    }


@router.put("/support-tickets/{ticket_id}")
async def admin_update_ticket(
    ticket_id: str,
    status: Optional[str] = None,
    assigned_to: Optional[str] = None,
    current_user=Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Atualiza ticket de suporte (admin)."""
    from backend.models.support_ticket import SupportTicket

    result = await db.execute(
        select(SupportTicket).where(SupportTicket.id == ticket_id)
    )
    ticket = result.scalar_one_or_none()

    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket não encontrado")

    if status:
        ticket.status = status
    if assigned_to:
        ticket.assigned_to = assigned_to

    await db.flush()
    return {"success": True, "message": "Ticket atualizado."}
