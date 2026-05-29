from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import String, Integer, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base


class LicenseStatus(str, Enum):
    """License lifecycle states."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"
    REVOKED = "revoked"
    SUSPENDED = "suspended"
    PENDING = "pending"


class License(Base):
    __tablename__ = "licenses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    license_key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    key_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    plan_id: Mapped[str] = mapped_column(String(36), ForeignKey("plans.id", ondelete="CASCADE"), nullable=False, index=True)
    signature: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False, index=True)
    hardware_fingerprint: Mapped[str] = mapped_column(String(64), default="", nullable=False)
    machine_id: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    activated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    revoke_reason: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    transfer_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_validated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    is_trial: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="licenses", lazy="select")
    plan: Mapped["Plan"] = relationship("Plan", back_populates="licenses", lazy="select")
    subscriptions: Mapped[list["Subscription"]] = relationship("Subscription", back_populates="license", cascade="all, delete-orphan", lazy="select")

    def __repr__(self):
        return f"<License(key={self.license_key[:12]}..., status={self.status})>"

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


class LicenseTransferHistory(Base):
    __tablename__ = "license_transfer_history"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    license_id: Mapped[str] = mapped_column(String(36), ForeignKey("licenses.id", ondelete="CASCADE"), nullable=False, index=True)
    from_user_id: Mapped[str] = mapped_column(String(36), nullable=True)
    to_user_id: Mapped[str] = mapped_column(String(36), nullable=True)
    old_hardware_fingerprint: Mapped[str] = mapped_column(String(64), default="")
    new_hardware_fingerprint: Mapped[str] = mapped_column(String(64), default="")
    reason: Mapped[str] = mapped_column(String(255), default="")
    transferred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    license_ref: Mapped["License"] = relationship("License", lazy="select")
