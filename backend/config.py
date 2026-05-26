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

    # ── AES-256 Encryption ────────────────────────────────
    ENCRYPTION_MASTER_KEY: str = Field(default="flora-32-byte-encryption-key!!")
    """Master key for AES-256-GCM encryption (license files, sensitive data)."""
    ENCRYPTION_KEY_VERSION: int = Field(default=1)
    """Current encryption key version for key rotation tracking."""

    # ── License ───────────────────────────────────────────
    LICENSE_ENCRYPTION_KEY: str = Field(default="flora-license-encrypt-key!!")
    """Dedicated key for encrypting license files."""
    LICENSE_GRACE_PERIOD_DAYS: int = Field(default=7)
    """Grace period in days after license expires."""
    LICENSE_MAX_MACHINES: int = Field(default=1)
    """Maximum number of machines per license."""
    LICENSE_MAX_TRANSFERS: int = Field(default=3)
    """Maximum number of license transfers allowed."""

    # ── Session / Token ───────────────────────────────────
    SESSION_TIMEOUT_MINUTES: int = Field(default=60)
    """Inactive session timeout in minutes."""
    TOKEN_BLACKLIST_ENABLED: bool = Field(default=True)
    """Enable token blacklisting on logout."""
    TOTP_ISSUER: str = Field(default="Flora Platform")
    """Issuer name for TOTP 2FA QR codes."""

    # ── Argon2 / Password Hashing ─────────────────────────
    ARGON2_TIME_COST: int = Field(default=3)
    """Argon2 time cost (iterations)."""
    ARGON2_MEMORY_COST: int = Field(default=65536)
    """Argon2 memory cost in KiB (64 MB)."""
    ARGON2_PARALLELISM: int = Field(default=4)
    """Argon2 parallelism factor."""
    PASSWORD_MIN_LENGTH: int = Field(default=8)
    """Minimum password length."""
    PASSWORD_REQUIRE_SPECIAL: bool = Field(default=True)
    """Require special characters in passwords."""

    # ── Rate Limiting ─────────────────────────────────────
    RATE_LIMIT_LOGIN_MAX: int = Field(default=5)
    """Max login attempts per lockout window."""
    RATE_LIMIT_LOGIN_WINDOW: int = Field(default=900)
    """Login rate limit window in seconds (15 min)."""
    RATE_LIMIT_API_MAX: int = Field(default=100)
    """Max API requests per window."""
    RATE_LIMIT_API_WINDOW: int = Field(default=60)
    """API rate limit window in seconds."""

    # ── App ───────────────────────────────────────────────
    APP_NAME: str = Field(default="Flora Platform")
    APP_VERSION: str = Field(default="1.0.0")
    ENVIRONMENT: str = Field(default="development")

    # ── Banco de Dados ─────────────────────────────────────
    DATABASE_URL: str = Field(default="sqlite+aiosqlite:///./flora.db")
    DB_ECHO: bool = Field(default=False)
    DB_POOL_SIZE: int = Field(default=10)
    DB_MAX_OVERFLOW: int = Field(default=20)

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
    WHATSAPP_WEBHOOK_SECRET: str = Field(default="")
    WHATSAPP_CONNECTOR_TOKEN: str = Field(default="")
    WHATSAPP_MAX_SESSIONS_PER_USER: int = Field(default=3)
    WHATSAPP_RATE_LIMIT_PER_MINUTE: int = Field(default=15)
    WHATSAPP_QR_EXPIRY_SECONDS: int = Field(default=60)

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

    @field_validator("ENCRYPTION_MASTER_KEY", "LICENSE_ENCRYPTION_KEY")
    @classmethod
    def validate_encryption_keys(cls, v: str, info) -> str:
        """Validate encryption keys are not default/weak values."""
        weak_values = [
            "flora-32-byte-encryption-key!!",
            "flora-license-encrypt-key!!",
            "change-me", "secret", "password", "123456",
        ]
        if v.lower() in weak_values:
            import warnings
            warnings.warn(
                f"{info.field_name} is using a default value. "
                "Set a strong unique key in production!",
                stacklevel=2,
            )
        return v

    @field_validator("PASSWORD_MIN_LENGTH")
    @classmethod
    def validate_password_min_length(cls, v: int) -> int:
        if v < 6:
            raise ValueError("PASSWORD_MIN_LENGTH must be at least 6")
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Instância global de configurações
settings = Settings()
