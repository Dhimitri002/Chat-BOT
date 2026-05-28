#!/usr/bin/env python3
"""
Script para criar o usuario administrador inicial da Flora Platform.

Variaveis de ambiente (ou usa valores padrao):
    ADMIN_EMAIL, ADMIN_PASSWORD, ADMIN_NAME

Uso:
    python -m backend.scripts.create_admin
    ADMIN_EMAIL=admin@test.com ADMIN_PASSWORD=123 python -m backend.scripts.create_admin
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from backend.config import settings
from backend.database import AsyncSessionLocal
from backend.models import User
from backend.core.security import get_password_hash, generate_api_key_endpoints


async def create_admin() -> None:
    """Cria o usuario admin padrao se ele ainda nao existir."""
    email = settings.ADMIN_EMAIL or "admin@flora.local"
    password = settings.ADMIN_PASSWORD or "admin123"
    name = settings.ADMIN_NAME or "Flora Admin"

    async with AsyncSessionLocal() as session:
        # Verifica se o admin ja existe
        result = await session.execute(select(User).where(User.email == email))
        existing = result.scalar_one_or_none()

        if existing:
            print(f"[create_admin] Usuario admin '{email}' ja existe (ID: {existing.id})")
            return

        admin = User(
            email=email,
            name=name,
            hashed_password=get_password_hash(password),
            is_admin=True,
            is_active=True,
            api_key=generate_api_key_endpoints(),
        )

        session.add(admin)
        await session.commit()
        await session.refresh(admin)

        print(f"[create_admin] Admin criado com sucesso!")
        print(f"  ID:    {admin.id}")
        print(f"  Nome:  {admin.name}")
        print(f"  Email: {admin.email}")
        print(f"  Role:  {'admin' if admin.is_admin else 'user'}")


if __name__ == "__main__":
    asyncio.run(create_admin())
