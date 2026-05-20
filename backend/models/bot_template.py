"""
Flora Platform — Bot Template Model
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Integer, Boolean, DateTime, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column
from backend.models.base import Base


class BotTemplate(Base):
    __tablename__ = "bot_templates"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # restaurant, clinic, salon, store, etc.
    icon: Mapped[str] = mapped_column(String(50), default="🤖", nullable=False)
    config: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    system_prompt: Mapped[str] = mapped_column(Text, default="", nullable=False)
    intents: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    commands: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    welcome_message: Mapped[str] = mapped_column(Text, default="", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    use_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    def __repr__(self):
        return f"<BotTemplate(name={self.name}, category={self.category})>"
