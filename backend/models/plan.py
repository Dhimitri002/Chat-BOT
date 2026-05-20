"""
Flora Platform — Plan Model
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Integer, Float, Boolean, DateTime, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.models.base import Base


class Plan(Base):
    __tablename__ = "plans"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    price_monthly: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    price_yearly: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    max_bots: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    max_messages_per_month: Mapped[int] = mapped_column(Integer, nullable=False, default=500)
    max_intents: Mapped[int] = mapped_column(Integer, nullable=False, default=20)
    max_commands: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    max_memory_items: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    has_llm: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    llm_provider: Mapped[str] = mapped_column(String(50), default="", nullable=False)
    llm_model: Mapped[str] = mapped_column(String(100), default="", nullable=False)
    llm_tokens_per_day: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    has_flora_ai: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_media: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_pdf: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_image: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_audio: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_transcription: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_webhooks: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_api_access: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_analytics: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_white_label: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_campaigns: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_multi_agent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    priority_support: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_public: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    features_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    subscriptions: Mapped[list["Subscription"]] = relationship("Subscription", back_populates="plan", lazy="select")
    licenses: Mapped[list["License"]] = relationship("License", back_populates="plan", lazy="select")

    def __repr__(self):
        return f"<Plan(name={self.name}, price_monthly={self.price_monthly})>"
