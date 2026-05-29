"""
Flora Platform — Conversation Model
====================================
Represents a conversation thread between a bot and a contact.
"""
from datetime import datetime, timezone
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from typing import List, Optional
from backend.models.base import Base


class Conversation(Base):
    """A conversation thread between a bot and a WhatsApp contact."""

    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    bot_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    contact_phone: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    contact_name: Mapped[str] = mapped_column(String(200), default="")

    last_message: Mapped[str] = mapped_column(Text, default="")
    last_message_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    unread_count: Mapped[int] = mapped_column(Integer, default=0)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # ── Relationships ────────────────────────────────────────────
    messages: Mapped[List["Message"]] = relationship(
        "Message", back_populates="conversation", lazy="select",
    )

    def __repr__(self):
        return f"<Conversation {self.id} bot={self.bot_id} contact={self.contact_phone}>"
