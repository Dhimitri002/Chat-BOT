"""
Flora Platform — Webhook Model
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Integer, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.models.base import Base


class Webhook(Base):
    __tablename__ = "webhooks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    bot_id: Mapped[str] = mapped_column(String(36), ForeignKey("bots.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    secret: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    events: Mapped[list] = mapped_column(JSON, default=list, nullable=False)  # message.received, bot.connected, etc.
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    success_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    fail_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_triggered: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[str] = mapped_column(Text, default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    bot: Mapped["Bot"] = relationship("Bot", lazy="select")

    def __repr__(self):
        return f"<Webhook(name={self.name}, url={self.url[:30]})>"
