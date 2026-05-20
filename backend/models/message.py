"""
Flora Platform — Message Model
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Integer, DateTime, Text, ForeignKey, Float, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.models.base import Base


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    bot_id: Mapped[str] = mapped_column(String(36), ForeignKey("bots.id", ondelete="CASCADE"), nullable=False, index=True)
    user_phone: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    direction: Mapped[str] = mapped_column(String(10), nullable=False, index=True)  # inbound, outbound
    content: Mapped[str] = mapped_column(Text, nullable=False)
    message_type: Mapped[str] = mapped_column(String(20), default="text", nullable=False)  # text, image, audio, video, document
    media_url: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    intent_matched: Mapped[str] = mapped_column(String(100), default="", nullable=False)
    command_used: Mapped[str] = mapped_column(String(100), default="", nullable=False)
    llm_model_used: Mapped[str] = mapped_column(String(100), default="", nullable=False)
    llm_tokens_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    llm_cost: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    whatsapp_message_id: Mapped[str] = mapped_column(String(100), default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    # Relationships
    bot: Mapped["Bot"] = relationship("Bot", back_populates="messages", lazy="select")

    def __repr__(self):
        return f"<Message(bot={self.bot_id}, direction={self.direction})>"
