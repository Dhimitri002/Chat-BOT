"""
Flora Platform — Database Connection & Session Management
"""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from backend.config import settings
from backend.models.base import Base
import os

# Configurar engine baseado no tipo de banco
if settings.database_url.startswith("sqlite"):
    engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=settings.debug,
    )
    # Habilitar WAL mode para melhor concorrência no SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.close()
else:
    # PostgreSQL ou outro
    engine = create_engine(
        settings.database_url,
        pool_size=20,
        max_overflow=10,
        pool_pre_ping=True,
        echo=settings.debug,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Dependency que fornece uma sessão do banco de dados."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_all_tables():
    """Cria todas as tabelas no banco de dados."""
    # Importar todos os models para registrar no metadata
    from backend.models import (  # noqa: F401
        User, Plan, Subscription, License, Bot, WhatsAppSession,
        Intent, Command, Memory, Message, LLMUsage, AuditLog,
        SystemEvent, BotTemplate, SupportTicket, Webhook,
        Notification, FloraSession, Payment,
    )
    Base.metadata.create_all(bind=engine)


def drop_all_tables():
    """Remove todas as tabelas (uso em testes)."""
    Base.metadata.drop_all(bind=engine)


def check_db_health() -> dict:
    """Verifica a saúde do banco de dados."""
    try:
        db = SessionLocal()
        db.execute(db.bind.dialect.statement_compiler(db.bind.dialect, None).__class__.__module__.startswith("sqlite") and "SELECT 1" or "SELECT 1")
        db.close()
        return {"status": "healthy", "database": settings.database_url.split("://")[0]}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
