"""
Flora Platform — Payment Model
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Float, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.models.base import Base


class PaymentStatus:
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELED = "canceled"


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    subscription_id: Mapped[str] = mapped_column(String(36), ForeignKey("subscriptions.id", ondelete="SET NULL"), nullable=True, index=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="BRL", nullable=False)
    status: Mapped[str] = mapped_column(String(20), default=PaymentStatus.PENDING, nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)  # stripe, mercadopago
    provider_payment_id: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    provider_charge_id: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    payment_method: Mapped[str] = mapped_column(String(50), default="", nullable=False)  # credit_card, pix, boleto
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    paid_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    refunded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    refund_reason: Mapped[str] = mapped_column(Text, default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", lazy="select")
    subscription: Mapped["Subscription"] = relationship("Subscription", lazy="select")

    def __repr__(self):
        return f"<Payment(amount={self.amount}, status={self.status})>"
