"""
Flora Platform — WhatsApp Session Model
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, ForeignKey, JSON, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.models.base import Base


class SessionStatus:
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    WAITING_QR = "waiting_qr"
    SCANNING = "scanning"
    CONNECTED = "connected"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class WhatsAppSession(Base):
    __tablename__ = "whatsapp_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    bot_id: Mapped[str] = mapped_column(String(36), ForeignKey("bots.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    session_name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    session_data: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    qr_code: Mapped[str] = mapped_column(Text, default="", nullable=False)
    qr_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default=SessionStatus.DISCONNECTED, nullable=False, index=True)
    phone_number: Mapped[str] = mapped_column(String(20), default="", nullable=False)
    phone_name: Mapped[str] = mapped_column(String(100), default="", nullable=False)
    connected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    disconnected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    disconnect_reason: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    reconnect_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[str] = mapped_column(Text, default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    bot: Mapped["Bot"] = relationship(
        "Bot",
        lazy="select",
        foreign_keys="[WhatsAppSession.bot_id]",
    )

    def __repr__(self):
        return f"<WhatsAppSession(bot={self.bot_id}, status={self.status})>"
