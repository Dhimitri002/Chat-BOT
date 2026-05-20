"""
Flora Platform — Subscription Model
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Boolean, Float, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.models.base import Base


class SubscriptionStatus:
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELED = "canceled"
    PAUSED = "paused"
    PAST_DUE = "past_due"
    TRIAL = "trial"


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    plan_id: Mapped[str] = mapped_column(String(36), ForeignKey("plans.id", ondelete="CASCADE"), nullable=False, index=True)
    license_id: Mapped[str] = mapped_column(String(36), ForeignKey("licenses.id", ondelete="SET NULL"), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(20), default=SubscriptionStatus.ACTIVE, nullable=False, index=True)
    billing_cycle: Mapped[str] = mapped_column(String(10), default="monthly", nullable=False)  # monthly, yearly
    price_paid: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="BRL", nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    canceled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    auto_renew: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    payment_method: Mapped[str] = mapped_column(String(50), default="", nullable=False)
    payment_provider: Mapped[str] = mapped_column(String(50), default="", nullable=False)  # stripe, mercadopago
    payment_provider_id: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    last_payment_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    next_payment_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    grace_period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    cancellation_reason: Mapped[str] = mapped_column(Text, default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="subscriptions", lazy="select")
    plan: Mapped["Plan"] = relationship("Plan", back_populates="subscriptions", lazy="select")
    license: Mapped["License"] = relationship("License", back_populates="subscriptions", lazy="select")

    def __repr__(self):
        return f"<Subscription(user={self.user_id}, plan={self.plan_id}, status={self.status})>"
