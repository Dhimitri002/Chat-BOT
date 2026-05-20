"""
Flora Platform — User Model
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Boolean, DateTime, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.models.base import Base
import enum


class UserRole(str, enum.Enum):
    USER = "user"
    ADMIN = "admin"
    SUPERADMIN = "superadmin"


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(SAEnum(UserRole), default=UserRole.USER, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_2fa_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    totp_secret: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    avatar_url: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    last_login: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    bots: Mapped[list["Bot"]] = relationship("Bot", back_populates="user", cascade="all, delete-orphan", lazy="select")
    licenses: Mapped[list["License"]] = relationship("License", back_populates="user", cascade="all, delete-orphan", lazy="select")
    subscriptions: Mapped[list["Subscription"]] = relationship("Subscription", back_populates="user", cascade="all, delete-orphan", lazy="select")
    audit_logs: Mapped[list["AuditLog"]] = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan", lazy="select")
    llm_usage: Mapped[list["LLMUsage"]] = relationship("LLMUsage", back_populates="user", cascade="all, delete-orphan", lazy="select")

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"
