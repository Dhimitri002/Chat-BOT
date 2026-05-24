"""WhatsApp Service - Serviço de gerenciamento de sessões WhatsApp no banco de dados."""
from datetime import datetime, timedelta
from typing import Optional
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.whatsapp_session import WhatsAppSession, SessionStatus


class WhatsAppService:
    """Serviço de persistência de sessões WhatsApp."""

    @staticmethod
    async def create_session(db: AsyncSession, bot_id: str, session_name: str = "") -> WhatsAppSession:
        """Cria uma nova sessão WhatsApp no banco."""
        session = WhatsAppSession(
            id=str(uuid4()),
            bot_id=bot_id,
            session_name=session_name or f"WhatsApp-{bot_id[:8]}",
            status=SessionStatus.DISCONNECTED,
            session_data={},
            reconnect_attempts=0,
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)
        return session

    @staticmethod
    async def get_session(db: AsyncSession, session_id: str) -> Optional[WhatsAppSession]:
        """Busca sessão por ID."""
        result = await db.execute(
            select(WhatsAppSession).where(WhatsAppSession.id == session_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_sessions(db: AsyncSession, bot_id: str) -> list[WhatsAppSession]:
        """Lista sessões de um bot."""
        result = await db.execute(
            select(WhatsAppSession)
            .where(WhatsAppSession.bot_id == bot_id)
            .order_by(WhatsAppSession.created_at.desc())
        )
        return result.scalars().all()

    @staticmethod
    async def update_qr(
        db: AsyncSession, session_id: str, qr_code: str, expires_in_seconds: int = 60
    ) -> bool:
        """Atualiza QR Code da sessão."""
        session = await WhatsAppService.get_session(db, session_id)
        if not session:
            return False

        session.qr_code = qr_code
        session.qr_expires_at = datetime.utcnow() + timedelta(seconds=expires_in_seconds)
        session.status = SessionStatus.QR_REQUIRED
        await db.commit()
        return True

    @staticmethod
    async def update_status(
        db: AsyncSession,
        session_id: str,
        status: SessionStatus,
        **kwargs,
    ) -> bool:
        """Atualiza status da sessão."""
        session = await WhatsAppService.get_session(db, session_id)
        if not session:
            return False

        session.status = status

        if status == SessionStatus.CONNECTED:
            session.connected_at = datetime.utcnow()
            session.phone_number = kwargs.get("phone_number")
            session.phone_name = kwargs.get("phone_name")
            session.reconnect_attempts = 0

        elif status == SessionStatus.DISCONNECTED:
            session.disconnected_at = datetime.utcnow()
            session.disconnect_reason = kwargs.get("reason")

        if "last_seen" in kwargs:
            session.last_seen = kwargs["last_seen"]
        elif status == SessionStatus.CONNECTED:
            session.last_seen = datetime.utcnow()

        await db.commit()
        return True

    @staticmethod
    async def disconnect_session(db: AsyncSession, session_id: str) -> bool:
        """Desconecta uma sessão."""
        return await WhatsAppService.update_status(
            db, session_id, SessionStatus.DISCONNECTED, reason="manual_disconnect"
        )

    @staticmethod
    async def delete_session(db: AsyncSession, session_id: str) -> bool:
        """Deleta uma sessão do banco."""
        session = await WhatsAppService.get_session(db, session_id)
        if not session:
            return False

        await db.delete(session)
        await db.commit()
        return True

    @staticmethod
    async def get_active_session(db: AsyncSession, bot_id: str) -> Optional[WhatsAppSession]:
        """Retorna sessão ativa de um bot."""
        result = await db.execute(
            select(WhatsAppSession).where(
                WhatsAppSession.bot_id == bot_id,
                WhatsAppSession.status == SessionStatus.CONNECTED,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def increment_reconnect(db: AsyncSession, session_id: str) -> int:
        """Incrementa contador de reconexão. Retorna novo valor."""
        session = await WhatsAppService.get_session(db, session_id)
        if not session:
            return 0

        session.reconnect_attempts = (session.reconnect_attempts or 0) + 1
        await db.commit()
        return session.reconnect_attempts

    @staticmethod
    async def cleanup_stale_sessions(db: AsyncSession, max_age_hours: int = 24) -> int:
        """Remove sessões antigas desconectadas."""
        cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
        result = await db.execute(
            select(WhatsAppSession).where(
                WhatsAppSession.status == SessionStatus.DISCONNECTED,
                WhatsAppSession.updated_at < cutoff,
            )
        )
        stale = result.scalars().all()

        for session in stale:
            await db.delete(session)

        if stale:
            await db.commit()

        return len(stale)
