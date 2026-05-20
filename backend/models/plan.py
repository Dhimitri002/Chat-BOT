"""Plan Model"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Boolean, Integer, Float, DateTime, Text, Numeric
from sqlalchemy.orm import Mapped, mapped_column
from backend.database import Base


class Plan(Base):
    __tablename__ = "plans"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    price_monthly: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    price_yearly: Mapped[float] = mapped_column(Numeric(10, 2), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="BRL")

    # Limits
    max_bots: Mapped[int] = mapped_column(Integer, default=1)
    max_messages_month: Mapped[int] = mapped_column(Integer, default=1000)
    max_commands: Mapped[int] = mapped_column(Integer, default=50)
    max_file_size_mb: Mapped[int] = mapped_column(Integer, default=5)
    max_memory_items: Mapped[int] = mapped_column(Integer, default=100)

    # Features
    has_llm: Mapped[bool] = mapped_column(Boolean, default=False)
    llm_provider: Mapped[str] = mapped_column(String(50), nullable=True)
    llm_model: Mapped[str] = mapped_column(String(100), nullable=True)
    llm_max_tokens: Mapped[int] = mapped_column(Integer, default=2048)
    has_media: Mapped[bool] = mapped_column(Boolean, default=False)
    has_pdf: Mapped[bool] = mapped_column(Boolean, default=False)
    has_image: Mapped[bool] = mapped_column(Boolean, default=False)
    has_audio: Mapped[bool] = mapped_column(Boolean, default=False)
    has_transcription: Mapped[bool] = mapped_column(Boolean, default=False)
    has_flora: Mapped[bool] = mapped_column(Boolean, default=False)
    flora_model: Mapped[str] = mapped_column(String(100), nullable=True)
    has_custom_commands: Mapped[bool] = mapped_column(Boolean, default=False)
    has_automations: Mapped[bool] = mapped_column(Boolean, default=False)
    has_webhooks: Mapped[bool] = mapped_column(Boolean, default=False)
    has_analytics: Mapped[bool] = mapped_column(Boolean, default=False)
    has_priority_support: Mapped[bool] = mapped_column(Boolean, default=False)
    has_whitelabel: Mapped[bool] = mapped_column(Boolean, default=False)
    has_api_access: Mapped[bool] = mapped_column(Boolean, default=False)
    has_multi_device: Mapped[bool] = mapped_column(Boolean, default=False)

    # Control
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
