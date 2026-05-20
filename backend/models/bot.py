"""
Flora Platform — Bot Model
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Integer, Float, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.models.base import Base


class BotStatus:
    DISCONNECTED = "disconnected"
    CONNECTED = "connected"
    PAUSED = "paused"
    ERROR = "error"


class Bot(Base):
    __tablename__ = "bots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    whatsapp_session_id: Mapped[str] = mapped_column(String(36), ForeignKey("whatsapp_sessions.id", ondelete="SET NULL"), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(20), default=BotStatus.DISCONNECTED, nullable=False, index=True)
    config: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    system_prompt: Mapped[str] = mapped_column(Text, default="", nullable=False)
    command_prefix: Mapped[str] = mapped_column(String(5), default="/", nullable=False)
    llm_model: Mapped[str] = mapped_column(String(100), default="", nullable=False)
    llm_provider: Mapped[str] = mapped_column(String(50), default="", nullable=False)
    llm_temperature: Mapped[float] = mapped_column(Float, default=0.7, nullable=False)
    llm_max_tokens: Mapped[int] = mapped_column(Integer, default=500, nullable=False)
    welcome_message: Mapped[str] = mapped_column(Text, default="Olá! 👋 Como posso te ajudar?", nullable=False)
    goodbye_message: Mapped[str] = mapped_column(Text, default="Até mais! 👋", nullable=False)
    error_message: Mapped[str] = mapped_column(Text, default="Desculpe, ocorreu um erro. Tente novamente.", nullable=False)
    fallback_message: Mapped[str] = mapped_column(Text, default="Não entendi. Pode reformular?", nullable=False)
    is_24h_mode: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    business_hours: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    max_messages_per_day: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # 0 = usar limite do plano
    personality: Mapped[str] = mapped_column(String(50), default="friendly", nullable=False)
    language: Mapped[str] = mapped_column(String(10), default="pt-BR", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="bots", lazy="select")
    whatsapp_session: Mapped["WhatsAppSession"] = relationship("WhatsAppSession", back_populates="bot", uselist=False, lazy="select")
    intents: Mapped[list["Intent"]] = relationship("Intent", back_populates="bot", cascade="all, delete-orphan", lazy="select")
    commands: Mapped[list["Command"]] = relationship("Command", back_populates="bot", cascade="all, delete-orphan", lazy="select")
    memories: Mapped[list["Memory"]] = relationship("Memory", back_populates="bot", cascade="all, delete-orphan", lazy="select")
    messages: Mapped[list["Message"]] = relationship("Message", back_populates="bot", cascade="all, delete-orphan", lazy="select")
    llm_usage: Mapped[list["LLMUsage"]] = relationship("LLMUsage", back_populates="bot", cascade="all, delete-orphan", lazy="select")

    def __repr__(self):
        return f"<Bot(name={self.name}, status={self.status})>"
