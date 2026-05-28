#!/usr/bin/env python3
"""
Script de inicialização do banco de dados Flora Platform.

Cria todas as tabelas definidas nos modelos SQLAlchemy.
Uso: python -m backend.scripts.init_db
"""

import asyncio
import sys
import os

# Garante que o diretorio raiz do backend esteja no path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import engine, Base
from backend.models import (
    User, Bot, License, Plan, Subscription,
    Conversation, Message, Command, Intent,
    Memory, FloraSession, WhatsAppSession, WhatsAppEvent,
    AuditLog, LLMUsage, Payment, SupportTicket,
    Notification, SystemEvent, BotTemplate, Webhook,
)


async def init_database() -> None:
    """Cria todas as tabelas do banco de dados."""
    print("[init_db] Inicializando banco de dados...")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print("[init_db] Tabelas criadas com sucesso!")
    print(f"[init_db] Engine: {engine.url}")


async def drop_database() -> None:
    """Remove todas as tabelas — USE COM CAUTELA."""
    print("[init_db] ATENCAO: Removendo todas as tabelas...")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    print("[init_db] Tabelas removidas.")


if __name__ == "__main__":
    if "--drop" in sys.argv:
        asyncio.run(drop_database())
    else:
        asyncio.run(init_database())
