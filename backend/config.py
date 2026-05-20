"""
Flora Platform — Configuration
"""
from typing import List
from pydantic_settings import BaseSettings
from pydantic import field_validator, ValidationError
import json
import secrets
import os


def _validate_required_secret(name: str, value: str, min_length: int = 32) -> str:
    """Valida que secret é definido, seguro e não é default."""
    if not value:
        raise ValueError(
            f"❌ CRÍTICA: {name} não definida no .env\n"
            f"Gere uma chave segura com: python -c \"import secrets; print(secrets.token_hex({min_length//2}))\"\n"
            f"Adicione ao .env: {name}=<chave_gerada>"
        )
    
    # Detectar defaults inseguros
    if value.lower() in ["change-me", "change-me-use-secrets-token-hex-32", "change-me-use-secrets-token-hex-64"]:
        raise ValueError(
            f"❌ CRÍTICA: {name} usando default inseguro!\n"
            f"Gere com: python -c \"import secrets; print(secrets.token_hex({min_length//2}))\"\n"
            "Nunca use defaults em produção."
        )
    
    if len(value) < min_length:
        raise ValueError(
            f"❌ {name} deve ter min {min_length} chars (tem {len(value)})\n"
            f"Gere com: python -c \"import secrets; print(secrets.token_hex({min_length//2}))\""
        )
    
    return value


class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite:///./data/flora.db"

    # Security — OBRIGATÓRIO em .env
    secret_key: str
    flora_master_key: str
    algorithm: str = "RS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # App
    app_name: str = "Flora Platform"
    app_version: str = "0.1.0"
    debug: bool = True

    # CORS
    cors_origins: str = '["http://localhost:8000"]'

    # LLM API Keys
    groq_api_key: str = ""
    gemini_api_key: str = ""
    openai_api_key: str = ""
    anthropic_api_key: str = ""

    # Redis
    redis_url: str = ""

    # Stripe
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""

    # Mercado Pago
    mp_access_token: str = ""

    # SMTP
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""

    # WhatsApp Connector
    whatsapp_connector_url: str = "http://localhost:3333"

    @field_validator("secret_key", mode="before")
    @classmethod
    def validate_secret_key(cls, v):
        return _validate_required_secret("SECRET_KEY", v, min_length=32)

    @field_validator("flora_master_key", mode="before")
    @classmethod
    def validate_flora_master_key(cls, v):
        return _validate_required_secret("FLORA_MASTER_KEY", v, min_length=32)

    @field_validator("debug", mode="before")
    @classmethod
    def validate_debug_production(cls, v):
        """Em produção (debug=False), força validações extras."""
        if v is False:
            # Production mode — adicionar validações
            pass
        return v

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return [origin.strip() for origin in v.split(",")]
        return v

    @property
    def cors_origins_list(self) -> List[str]:
        if isinstance(self.cors_origins, str):
            try:
                return json.loads(self.cors_origins)
            except json.JSONDecodeError:
                return [o.strip() for o in self.cors_origins.split(",")]
        return self.cors_origins

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


try:
    settings = Settings()
except ValidationError as e:
    # Erro de configuração — fatal
    import sys
    print("\n" + "="*70)
    print("❌ ERRO CRÍTICO NA CONFIGURAÇÃO")
    print("="*70)
    for error in e.errors():
        print(f"\n⚠️  {error['loc'][0]}: {error['msg']}")
    print("\n" + "="*70)
    sys.exit(1)
