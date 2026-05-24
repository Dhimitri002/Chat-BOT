"""Configuração da aplicação — Carrega variáveis de ambiente com validação."""
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configurações da aplicação carregadas do .env."""

    # ── Segurança (OBRIGATÓRIO) ──────────────────────────
    SECRET_KEY: str = Field(..., min_length=32)
    FLORA_MASTER_KEY: str = Field(..., min_length=32)
    LICENSE_SIGNING_KEY: str = Field(..., min_length=32)

    # ── App ───────────────────────────────────────────────
    APP_NAME: str = Field(default="Flora Platform")
    APP_VERSION: str = Field(default="1.0.0")
    ENVIRONMENT: str = Field(default="development")

    # ── Banco de Dados ─────────────────────────────────────
    DATABASE_URL: str = Field(default="sqlite+aiosqlite:///./flora.db")

    # ── Redis ──────────────────────────────────────────────
    REDIS_URL: str = Field(default="redis://localhost:6379")

    # ── Servidor ───────────────────────────────────────────
    DEBUG: bool = Field(default=False)
    HOST: str = Field(default="0.0.0.0")
    PORT: int = Field(default=8000)
    ALLOWED_ORIGINS: list[str] = Field(default=["*"])
    CORS_ORIGINS: list[str] = Field(default=["*"])

    # ── JWT ────────────────────────────────────────────────
    JWT_ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7)

    # ── LLMs ───────────────────────────────────────────────
    LLM_PROVIDER: str = Field(default="groq")
    GROQ_API_KEY: Optional[str] = Field(default=None)
    GEMINI_API_KEY: Optional[str] = Field(default=None)
    OPENAI_API_KEY: Optional[str] = Field(default=None)
    ANTHROPIC_API_KEY: Optional[str] = Field(default=None)
    OPENROUTER_API_KEY: Optional[str] = Field(default=None)

    # ── WhatsApp ───────────────────────────────────────────
    WHATSAPP_API_URL: str = Field(default="")
    WHATSAPP_API_TOKEN: str = Field(default="")

    # ── Logging ────────────────────────────────────────────
    LOG_LEVEL: str = Field(default="INFO")

    # ── Backup ─────────────────────────────────────────────
    BACKUP_ENCRYPTION_KEY: Optional[str] = Field(default=None)
    ENCRYPTION_KEY: Optional[str] = Field(default="flora-32-byte-encryption-key!!")

    # ── Suporte ────────────────────────────────────────────
    SUPPORT_EMAIL: str = Field(default="support@flora.bot")

    # ── Rate Limiting ──────────────────────────────────────
    RATE_LIMIT_REQUESTS: int = Field(default=100)
    RATE_LIMIT_WINDOW: int = Field(default=60)
    RATE_LIMIT_PER_MINUTE: int = Field(default=60)

    # ── Login ──────────────────────────────────────────────
    LOGIN_MAX_ATTEMPTS: int = Field(default=5)
    LOGIN_LOCKOUT_MINUTES: int = Field(default=15)

    # ── WhatsApp ───────────────────────────────────────────
    WHATSAPP_SESSION_DIR: str = Field(default="./sessions")
    WHATSAPP_CONNECTOR_URL: str = Field(default="http://localhost:3333")

    @field_validator("SECRET_KEY", "FLORA_MASTER_KEY", "LICENSE_SIGNING_KEY")
    @classmethod
    def validate_secret_keys(cls, v: str, info) -> str:
        """Valida que chaves secretas não são valores padrão/fracos."""
        weak_values = [
            "change-me", "secret", "password", "123456", "admin",
            "default", "test", "your-secret-key", "insecure",
            "super-secret-key-change-in-production",
        ]
        if v.lower() in weak_values:
            raise ValueError(
                f"{info.field_name} deve ser uma chave segura, não '{v}'"
            )
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Instância global de configurações
settings = Settings()
