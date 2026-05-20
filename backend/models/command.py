"""
Flora Platform — Command Model
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Integer, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.models.base import Base


class Command(Base):
    __tablename__ = "commands"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    bot_id: Mapped[str] = mapped_column(String(36), ForeignKey("bots.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    trigger: Mapped[str] = mapped_column(String(100), nullable=False)
    response: Mapped[str] = mapped_column(Text, default="", nullable=False)
    response_type: Mapped[str] = mapped_column(String(20), default="text", nullable=False)  # text, image, action
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    use_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    bot: Mapped["Bot"] = relationship("Bot", back_populates="commands", lazy="select")

    def __repr__(self):
        return f"<Command(name={self.name}, trigger={self.trigger})>"
