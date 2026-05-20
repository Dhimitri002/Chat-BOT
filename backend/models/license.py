"""
Flora Platform — License Model
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Integer, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.models.base import Base


class License(Base):
    __tablename__ = "licenses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    key: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    key_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    plan_id: Mapped[str] = mapped_column(String(36), ForeignKey("plans.id", ondelete="CASCADE"), nullable=False, index=True)
    signature: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False, index=True)
    device_fingerprint: Mapped[str] = mapped_column(String(64), default="", nullable=False)
    device_name: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    activated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    revoke_reason: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    max_devices: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    current_devices: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_trial: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    trial_activated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="licenses", lazy="select")
    plan: Mapped["Plan"] = relationship("Plan", back_populates="licenses", lazy="select")
    subscriptions: Mapped[list["Subscription"]] = relationship("Subscription", back_populates="license", cascade="all, delete-orphan", lazy="select")

    def __repr__(self):
        return f"<License(key={self.key[:12]}..., status={self.status})>"

    @property
    def is_active(self):
        if self.status != "active":
            return False
        if self.expires_at and self.expires_at < datetime.now(timezone.utc):
            return False
        return True

    @property
    def days_remaining(self):
        if not self.expires_at:
            return -1  # Ilimitado
        delta = self.expires_at - datetime.now(timezone.utc)
        return max(0, delta.days)
