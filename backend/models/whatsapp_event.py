"""
Flora Platform — WhatsApp Event Model
======================================
Logs all WhatsApp connection events: connection attempts, QR scans,
messages sent/received, errors, and disconnections.

Used for debugging, analytics, and audit trails.
"""
import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, DateTime, ForeignKey, JSON, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.models.base import Base


class EventType:
    """WhatsApp event types."""
    # Connection events
    CONNECTION_STARTED = "connection_started"
    CONNECTION_ESTABLISHED = "connection_established"
    CONNECTION_LOST = "connection_lost"
    CONNECTION_CLOSED = "connection_closed"
    RECONNECTION_STARTED = "reconnection_started"
    RECONNECTION_SUCCESS = "reconnection_success"
    RECONNECTION_FAILED = "reconnection_failed"
    LOGGED_OUT = "logged_out"

    # QR events
    QR_GENERATED = "qr_generated"
    QR_SCANNED = "qr_scanned"
    QR_EXPIRED = "qr_expired"
    QR_REFRESHED = "qr_refreshed"

    # Message events
    MESSAGE_SENT = "message_sent"
    MESSAGE_DELIVERED = "message_delivered"
    MESSAGE_READ = "message_read"
    MESSAGE_FAILED = "message_failed"
    MESSAGE_RECEIVED = "message_received"
    MESSAGE_REACTION = "message_reaction"

    # Error events
    ERROR = "error"
    RATE_LIMITED = "rate_limited"
    TIMEOUT = "timeout"
    AUTH_FAILURE = "auth_failure"

    # Session events
    SESSION_CREATED = "session_created"
    SESSION_DELETED = "session_deleted"
    SESSION_RESTORED = "session_restored"

    # Webhook events
    WEBHOOK_RECEIVED = "webhook_received"
    WEBHOOK_ERROR = "webhook_error"


class WhatsAppEvent(Base):
    """Stores a single WhatsApp-related event."""
    __tablename__ = "whatsapp_events"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    session_id: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True,
        comment="WhatsApp session ID (not the DB model ID)"
    )
    bot_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("bots.id", ondelete="CASCADE"),
        nullable=True, index=True
    )
    event_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )
    message: Mapped[str] = mapped_column(Text, default="", nullable=False)
    details: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    phone_number: Mapped[str] = mapped_column(String(20), default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    # Relationships
    bot: Mapped[Optional["Bot"]] = relationship("Bot", lazy="select")

    # Composite indexes for common queries
    __table_args__ = (
        Index("ix_wa_events_session_type", "session_id", "event_type"),
        Index("ix_wa_events_bot_type", "bot_id", "event_type"),
        Index("ix_wa_events_session_created", "session_id", "created_at"),
    )

    def __repr__(self):
        return f"<WhatsAppEvent(type={self.event_type}, session={self.session_id})>"
