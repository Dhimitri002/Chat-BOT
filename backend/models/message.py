"""Message Model"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Integer, DateTime, Text, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column
from backend.database import Base


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    bot_id: Mapped[str] = mapped_column(String(36), ForeignKey("bots.id"), nullable=False, index=True)
    contact_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    direction: Mapped[str] = mapped_column(String(10), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=True)
    message_type: Mapped[str] = mapped_column(String(20), default="text")
    media_url: Mapped[str] = mapped_column(Text, nullable=True)

    # LLM
    llm_provider: Mapped[str] = mapped_column(String(50), nullable=True)
    llm_model: Mapped[str] = mapped_column(String(100), nullable=True)
    llm_tokens_in: Mapped[int] = mapped_column(Integer, nullable=True)
    llm_tokens_out: Mapped[int] = mapped_column(Integer, nullable=True)
    llm_cost: Mapped[float] = mapped_column(Numeric(10, 6), nullable=True)
    llm_latency_ms: Mapped[int] = mapped_column(Integer, nullable=True)

    # Status
    status: Mapped[str] = mapped_column(String(20), default="sent")
    error: Mapped[str] = mapped_column(Text, nullable=True)

    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
