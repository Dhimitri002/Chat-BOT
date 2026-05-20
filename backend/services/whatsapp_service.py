"""
Flora Platform — WhatsApp Service
"""
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from backend.models.whatsapp_session import WhatsAppSession, SessionStatus
from backend.models.bot import Bot


class WhatsAppService:
    """Service for managing WhatsApp sessions and connections."""

    @staticmethod
    async def create_session(db: AsyncSession, bot_id: str) -> WhatsAppSession:
        """Create a new WhatsApp session for a bot."""
        # Verify bot exists
        result = await db.execute(select(Bot).where(Bot.id == bot_id))
        bot = result.scalar_one_or_none()
        if not bot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bot not found",
            )

        # Check if a session already exists for this bot
        existing = await db.execute(
            select(WhatsAppSession).where(WhatsAppSession.bot_id == bot_id)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A WhatsApp session already exists for this bot",
            )

        now = datetime.now(timezone.utc)
        session = WhatsAppSession(
            id=str(uuid.uuid4()),
            bot_id=bot_id,
            session_name=f"flora_{bot_id[:8]}",
            session_data={},
            qr_code="",
            qr_expires_at=None,
            status=SessionStatus.DISCONNECTED,
            phone_number="",
            phone_name="",
            connected_at=None,
            last_seen=None,
            disconnected_at=None,
            disconnect_reason="",
            reconnect_attempts="0",
            error_message="",
            created_at=now,
            updated_at=now,
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)
        return session

    @staticmethod
    async def get_session(db: AsyncSession, session_id: str) -> WhatsAppSession:
        """Get a WhatsApp session by its ID."""
        result = await db.execute(
            select(WhatsAppSession).where(WhatsAppSession.id == session_id)
        )
        session = result.scalar_one_or_none()

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found",
            )
        return session

    @staticmethod
    async def get_session_by_bot(db: AsyncSession, bot_id: str) -> Optional[WhatsAppSession]:
        """Get the WhatsApp session associated with a bot."""
        result = await db.execute(
            select(WhatsAppSession).where(WhatsAppSession.bot_id == bot_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def update_session_status(
        db: AsyncSession,
        session_id: str,
        status: str,
        **kwargs,
    ) -> WhatsAppSession:
        """Update the status of a WhatsApp session with optional additional fields."""
        session = await WhatsAppService.get_session(db, session_id)

        session.status = status
        session.updated_at = datetime.now(timezone.utc)

        # Handle known optional fields
        if "phone_number" in kwargs:
            session.phone_number = kwargs["phone_number"]
        if "phone_name" in kwargs:
            session.phone_name = kwargs["phone_name"]
        if "error_message" in kwargs:
            session.error_message = kwargs["error_message"]
        if "disconnect_reason" in kwargs:
            session.disconnect_reason = kwargs["disconnect_reason"]
        if "reconnect_attempts" in kwargs:
            session.reconnect_attempts = str(kwargs["reconnect_attempts"])

        # Set timestamps based on status transitions
        if status == SessionStatus.CONNECTED:
            session.connected_at = kwargs.get("connected_at", datetime.now(timezone.utc))
            session.last_seen = datetime.now(timezone.utc)
            session.disconnected_at = None
            session.disconnect_reason = ""
        elif status == SessionStatus.DISCONNECTED:
            session.disconnected_at = kwargs.get("disconnected_at", datetime.now(timezone.utc))
        elif status in (SessionStatus.WAITING_QR, SessionStatus.SCANNING):
            session.last_seen = datetime.now(timezone.utc)

        await db.commit()
        await db.refresh(session)
        return session

    @staticmethod
    async def update_qr_code(
        db: AsyncSession,
        session_id: str,
        qr_code: str,
        expires_at: datetime,
    ) -> WhatsAppSession:
        """Update the QR code for a WhatsApp session."""
        session = await WhatsAppService.get_session(db, session_id)

        session.qr_code = qr_code
        session.qr_expires_at = expires_at
        session.status = SessionStatus.WAITING_QR
        session.updated_at = datetime.now(timezone.utc)

        await db.commit()
        await db.refresh(session)
        return session

    @staticmethod
    async def list_sessions(db: AsyncSession, user_id: Optional[str] = None) -> list[WhatsAppSession]:
        """List all WhatsApp sessions, optionally filtered by user_id."""
        query = select(WhatsAppSession).order_by(WhatsAppSession.created_at.desc())

        if user_id is not None:
            # Join with Bot to filter by user
            query = (
                query.join(Bot, Bot.whatsapp_session_id == WhatsAppSession.id)
                .where(Bot.user_id == user_id)
            )

        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def delete_session(db: AsyncSession, session_id: str) -> dict:
        """Delete a WhatsApp session."""
        session = await WhatsAppService.get_session(db, session_id)

        # Clear the reference on the bot if linked
        bot_result = await db.execute(
            select(Bot).where(Bot.whatsapp_session_id == session_id)
        )
        bot = bot_result.scalar_one_or_none()
        if bot:
            bot.whatsapp_session_id = None
            bot.status = "disconnected"

        await db.delete(session)
        await db.commit()
        return {"success": True, "message": f"Session {session_id} deleted successfully"}

    @staticmethod
    async def get_active_sessions_count(db: AsyncSession, user_id: str) -> int:
        """Count the number of active (connected) sessions for a user, used for rate limiting."""
        result = await db.execute(
            select(func.count(WhatsAppSession.id))
            .join(Bot, Bot.whatsapp_session_id == WhatsAppSession.id)
            .where(Bot.user_id == user_id)
            .where(WhatsAppSession.status == SessionStatus.CONNECTED)
        )
        return result.scalar() or 0
