"""
Flora Platform — Notification Model
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.models.base import Base


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[str] = mapped_column(String(50), default="info", nullable=False)  # info, warning, error, success
    category: Mapped[str] = mapped_column(String(50), default="system", nullable=False)  # system, license, bot, billing
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    action_url: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    data: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    read_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    # Relationships
    user: Mapped["User"] = relationship("User", lazy="select")

    def __repr__(self):
        return f"<Notification(user={self.user_id}, title={self.title[:30]})>"
