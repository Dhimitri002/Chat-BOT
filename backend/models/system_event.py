"""
Flora Platform — System Event Model
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column
from backend.models.base import Base


class SystemEvent(Base):
    __tablename__ = "system_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(20), default="info", nullable=False, index=True)  # info, warning, error, critical
    message: Mapped[str] = mapped_column(Text, nullable=False)
    details: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    source: Mapped[str] = mapped_column(String(100), default="", nullable=False)  # backend, whatsapp, llm, etc.
    is_resolved: Mapped[bool] = mapped_column(String(36), default="False", nullable=False)
    resolved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    def __repr__(self):
        return f"<SystemEvent(type={self.event_type}, severity={self.severity})>"
