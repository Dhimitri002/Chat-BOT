"""
Flora Platform — Configuration
"""
from typing import List
from pydantic_settings import BaseSettings
from pydantic import field_validator
import json
import secrets


class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite:///./data/flora.db"

    # Security
    secret_key: str = secrets.token_hex(32)
    flora_master_key: str = secrets.token_hex(32)
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


settings = Settings()
