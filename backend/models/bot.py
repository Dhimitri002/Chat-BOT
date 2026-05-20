"""Bot Model"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Boolean, Integer, Float, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column
from backend.database import Base


class Bot(Base):
    __tablename__ = "bots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    license_id: Mapped[str] = mapped_column(String(36), ForeignKey("licenses.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    avatar_url: Mapped[str] = mapped_column(Text, nullable=True)

    # Personality
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    personality: Mapped[str] = mapped_column(String(50), default="friendly")
    tone: Mapped[str] = mapped_column(String(50), default="warm")
    language: Mapped[str] = mapped_column(String(10), default="pt-BR")

    # Config
    welcome_message: Mapped[str] = mapped_column(Text, nullable=True)
    farewell_message: Mapped[str] = mapped_column(Text, nullable=True)
    away_message: Mapped[str] = mapped_column(Text, nullable=True)
    business_hours: Mapped[dict] = mapped_column(JSON, nullable=True)
    timezone: Mapped[str] = mapped_column(String(50), default="America/Sao_Paulo")

    # LLM
    preferred_llm: Mapped[str] = mapped_column(String(50), nullable=True)
    temperature: Mapped[float] = mapped_column(Float, default=0.7)
    max_tokens: Mapped[int] = mapped_column(Integer, default=1024)

    # State
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_connected: Mapped[bool] = mapped_column(Boolean, default=False)

    # Metadata
    config: Mapped[dict] = mapped_column(JSON, default=dict)
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
