"""
Flora Platform — Notification Service
"""
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from backend.models.notification import Notification


class NotificationService:
    """Service for managing user notifications."""

    @staticmethod
    async def create_notification(
        db: AsyncSession,
        user_id: str,
        title: str,
        message: str,
        type: str = "info",
        category: str = "system",
        action_url: str = "",
        data: dict = None,
    ) -> Notification:
        """Create a new notification for a user."""
        now = datetime.now(timezone.utc)
        notification = Notification(
            id=str(uuid.uuid4()),
            user_id=user_id,
            title=title,
            message=message,
            type=type,
            category=category,
            is_read=False,
            action_url=action_url,
            data=data or {},
            read_at=None,
            created_at=now,
        )
        db.add(notification)
        await db.commit()
        await db.refresh(notification)
        return notification

    @staticmethod
    async def get_user_notifications(
        db: AsyncSession,
        user_id: str,
        unread_only: bool = False,
        limit: int = 50,
    ) -> list[Notification]:
        """Get notifications for a user, optionally only unread ones."""
        query = (
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
            .limit(limit)
        )

        if unread_only:
            query = query.where(Notification.is_read == False)

        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def mark_as_read(db: AsyncSession, notification_id: str) -> Notification:
        """Mark a single notification as read."""
        result = await db.execute(
            select(Notification).where(Notification.id == notification_id)
        )
        notification = result.scalar_one_or_none()

        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found",
            )

        notification.is_read = True
        notification.read_at = datetime.now(timezone.utc)

        await db.commit()
        await db.refresh(notification)
        return notification

    @staticmethod
    async def mark_all_as_read(db: AsyncSession, user_id: str) -> dict:
        """Mark all notifications as read for a user."""
        result = await db.execute(
            select(Notification)
            .where(Notification.user_id == user_id)
            .where(Notification.is_read == False)
        )
        unread_notifications = result.scalars().all()

        now = datetime.now(timezone.utc)
        count = 0
        for notification in unread_notifications:
            notification.is_read = True
            notification.read_at = now
            count += 1

        await db.commit()
        return {"success": True, "marked_as_read": count}

    @staticmethod
    async def get_unread_count(db: AsyncSession, user_id: str) -> int:
        """Get the count of unread notifications for a user."""
        result = await db.execute(
            select(func.count(Notification.id))
            .where(Notification.user_id == user_id)
            .where(Notification.is_read == False)
        )
        return result.scalar() or 0

    @staticmethod
    async def delete_old_notifications(db: AsyncSession, days: int = 30) -> dict:
        """Delete notifications older than the specified number of days."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        result = await db.execute(
            select(Notification).where(Notification.created_at < cutoff)
        )
        old_notifications = result.scalars().all()

        count = 0
        for notification in old_notifications:
            await db.delete(notification)
            count += 1

        await db.commit()
        return {"success": True, "deleted_count": count}

    @staticmethod
    async def notify_license_expiring(db: AsyncSession, user_id: str, days_left: int) -> Notification:
        """Create a notification about an expiring license."""
        if days_left <= 0:
            title = "Sua licença expirou"
            message = "Sua licença expirou. Renove agora para continuar usando todos os recursos."
            notif_type = "error"
        elif days_left == 1:
            title = "Sua licença expira amanhã"
            message = "Sua licença expira em 1 dia. Renove para não perder acesso."
            notif_type = "warning"
        else:
            title = f"Sua licença expira em {days_left} dias"
            message = f"Sua licença expira em {days_left} dias. Renove para continuar usando todos os recursos."
            notif_type = "warning"

        return await NotificationService.create_notification(
            db=db,
            user_id=user_id,
            title=title,
            message=message,
            type=notif_type,
            category="license",
            action_url="/billing",
            data={"days_left": days_left},
        )

    @staticmethod
    async def notify_payment_failed(db: AsyncSession, user_id: str, amount: float) -> Notification:
        """Create a notification about a failed payment."""
        return await NotificationService.create_notification(
            db=db,
            user_id=user_id,
            title="Pagamento não processado",
            message=f"Não foi possível processar seu pagamento de R$ {amount:.2f}. "
                    f"Verifique seus dados de pagamento e tente novamente.",
            type="error",
            category="billing",
            action_url="/billing",
            data={"amount": amount},
        )

    @staticmethod
    async def notify_bot_disconnected(db: AsyncSession, user_id: str, bot_name: str) -> Notification:
        """Create a notification about a bot disconnection."""
        return await NotificationService.create_notification(
            db=db,
            user_id=user_id,
            title=f"Bot {bot_name} desconectado",
            message=f"Seu bot '{bot_name}' foi desconectado do WhatsApp. "
                    f"Reconecte para continuar atendendo seus clientes.",
            type="warning",
            category="bot",
            action_url="/bots",
            data={"bot_name": bot_name},
        )
