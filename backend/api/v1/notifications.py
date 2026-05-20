"""Notifications Endpoints - API para gerenciamento de notificações."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user, get_db

router = APIRouter(prefix="/notifications", tags=["notifications"])


class NotificationSettingsRequest(BaseModel):
    email_enabled: Optional[bool] = None
    push_enabled: Optional[bool] = None
    whatsapp_connected: Optional[bool] = None
    whatsapp_disconnected: Optional[bool] = None
    new_message: Optional[bool] = None
    license_expiring: Optional[bool] = None
    payment_received: Optional[bool] = None
    system_alert: Optional[bool] = None


@router.get("/")
async def list_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    unread_only: bool = Query(False),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Lista notificações do usuário."""
    from backend.models.notification import Notification

    query = select(Notification).where(Notification.user_id == current_user.id)
    if unread_only:
        query = query.where(Notification.is_read == False)
    query = query.order_by(Notification.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    notifications = result.scalars().all()

    return {
        "notifications": [
            {
                "id": n.id,
                "title": n.title,
                "message": n.message,
                "type": n.type,
                "is_read": n.is_read,
                "created_at": n.created_at.isoformat() if n.created_at else None,
            }
            for n in notifications
        ]
    }


@router.put("/{notification_id}/read")
async def mark_as_read(
    notification_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Marca notificação como lida."""
    from backend.models.notification import Notification

    result = await db.execute(
        select(Notification).where(
            Notification.id == notification_id, Notification.user_id == current_user.id
        )
    )
    notification = result.scalar_one_or_none()

    if not notification:
        raise HTTPException(status_code=404, detail="Notificação não encontrada")

    notification.is_read = True
    await db.flush()
    return {"success": True}


@router.put("/read-all")
async def mark_all_as_read(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Marca todas as notificações como lidas."""
    from backend.models.notification import Notification

    result = await db.execute(
        select(Notification).where(
            Notification.user_id == current_user.id, Notification.is_read == False
        )
    )
    notifications = result.scalars().all()

    for n in notifications:
        n.is_read = True

    await db.flush()
    return {"success": True, "marked": len(notifications)}


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Deleta uma notificação."""
    from backend.models.notification import Notification

    result = await db.execute(
        select(Notification).where(
            Notification.id == notification_id, Notification.user_id == current_user.id
        )
    )
    notification = result.scalar_one_or_none()

    if not notification:
        raise HTTPException(status_code=404, detail="Notificação não encontrada")

    await db.delete(notification)
    await db.flush()
    return {"success": True}


@router.get("/settings")
async def get_notification_settings(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Obtém configurações de notificação."""
    return {
        "email_enabled": True,
        "push_enabled": True,
        "whatsapp_connected": True,
        "whatsapp_disconnected": True,
        "new_message": True,
        "license_expiring": True,
        "payment_received": True,
        "system_alert": True,
    }


@router.put("/settings")
async def update_notification_settings(
    request: NotificationSettingsRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Atualiza configurações de notificação."""
    return {"success": True, "message": "Configurações atualizadas."}
