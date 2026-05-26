"""
Flora Platform — Message Model
===============================
Stores all messages (incoming and outgoing) for a bot.
Tracks delivery status, media, AI processing metadata, and conversation threading.
"""
import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base


class Message(Base):
    __tablename__ = "messages"

    # ── Identity ─────────────────────────────────────────────────
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    bot_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("bots.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    conversation_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("conversations.id", ondelete="SET NULL"),
        nullable=True, index=True,
    )

    # ── Direction & Sender ───────────────────────────────────────
    direction: Mapped[str] = mapped_column(
        String(10), nullable=False, index=True,
    )  # "in" or "out"
    sender_phone: Mapped[str] = mapped_column(
        String(50), default="", nullable=False, index=True,
    )
    sender_name: Mapped[str] = mapped_column(
        String(200), default="", nullable=False,
    )
    user_phone: Mapped[str] = mapped_column(
        String(20), default="", nullable=False, index=True,
    )  # Legacy field, use sender_phone

    # ── Content ──────────────────────────────────────────────────
    content: Mapped[str] = mapped_column(Text, default="", nullable=False)
    message_type: Mapped[str] = mapped_column(
        String(20), default="text", nullable=False,
    )  # text, image, audio, video, document, sticker, location, contact, buttons, list, reaction, poll
    media_url: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    media_type: Mapped[str] = mapped_column(String(20), default="", nullable=False)
    media_caption: Mapped[str] = mapped_column(Text, default="", nullable=False)
    media_filename: Mapped[str] = mapped_column(String(255), default="", nullable=False)

    # ── WhatsApp Tracking ────────────────────────────────────────
    whatsapp_message_id: Mapped[str] = mapped_column(
        String(100), default="", nullable=False, index=True,
    )
    whatsapp_status: Mapped[str] = mapped_column(
        String(20), default="pending", nullable=False,
    )  # pending, sent, delivered, read, received, failed
    is_delivered: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # ── AI Processing ────────────────────────────────────────────
    intent_matched: Mapped[str] = mapped_column(String(100), default="", nullable=False)
    command_used: Mapped[str] = mapped_column(String(100), default="", nullable=False)
    llm_model_used: Mapped[str] = mapped_column(String(100), default="", nullable=False)
    llm_tokens_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    llm_cost: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # ── Raw Data ─────────────────────────────────────────────────
    raw_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # ── Timestamps ───────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False, index=True,
    )

    # ── Relationships ────────────────────────────────────────────
    bot: Mapped["Bot"] = relationship("Bot", back_populates="messages", lazy="select")
    conversation: Mapped["Conversation"] = relationship(
        "Conversation", back_populates="messages", lazy="select",
    )

    def __repr__(self):
        return f"<Message(id={self.id[:8]} bot={self.bot_id[:8]} dir={self.direction} type={self.message_type})>"
