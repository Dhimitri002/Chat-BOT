"""WhatsApp Session Model"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column
from backend.database import Base


class WhatsAppSession(Base):
    __tablename__ = "whatsapp_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    bot_id: Mapped[str] = mapped_column(String(36), ForeignKey("bots.id"), nullable=False, index=True)
    session_name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(20), nullable=True)
    qr_code: Mapped[str] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="disconnected")
    connected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    disconnected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    last_activity: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    device_info: Mapped[dict] = mapped_column(JSON, nullable=True)
    error_log: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
