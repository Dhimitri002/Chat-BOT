"""
Flora Platform — Memory Model (Bot Memory per User)
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Text, ForeignKey, JSON, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.models.base import Base


class Memory(Base):
    __tablename__ = "bot_memories"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    bot_id: Mapped[str] = mapped_column(String(36), ForeignKey("bots.id", ondelete="CASCADE"), nullable=False, index=True)
    user_phone: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    key: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    context: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    bot: Mapped["Bot"] = relationship("Bot", back_populates="memories", lazy="select")

    __table_args__ = (
        # Unique constraint: um memory key por bot+user
        UniqueConstraint("bot_id", "user_phone", "key", name="uq_bot_user_memory_key"),
        Index("ix_memory_expires_at", "expires_at"),
        {"sqlite_autoincrement": True},
    )

    def __repr__(self):
        return f"<Memory(bot={self.bot_id}, user={self.user_phone}, key={self.key})>"
