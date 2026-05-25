"""Configuração global dos testes — fixtures e setup."""
import asyncio

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from backend.main import app
from backend.models.base import Base

# Banco de dados em memória para testes
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_flora.db"
TEST_DATABASE_URL_ASYNC = "sqlite+aiosqlite+aiosqlite:///./test_flora.db"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="session")
def event_loop():
    """Cria um event loop para toda a sessão de testes."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    """Cria e destrói as tabelas para cada teste."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session() -> AsyncSession:
    """Fornece uma sessão de banco de dados para testes."""
    async with async_session_maker() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client():
    """Fornece um cliente HTTP assíncrono para testar a API."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession):
    """Cria um usuário admin para testes."""
    from backend.models.user import User

    user = User(
        name="Admin Test",
        email="admin@test.com",
        hashed_password="$2b$12$LJ3m4ys2Lg2VBe0E/R5XxOYqIGNPMGBOkgd6ZPbHOOQ/q7iAV7IqC",  # Admin@123
        is_admin=True,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def regular_user(db_session: AsyncSession):
    """Cria um usuário regular para testes."""
    from backend.models.user import User

    user = User(
        name="User Test",
        email="user@test.com",
        hashed_password="$2b$12$LJ3m4ys2Lg2VBe0E/R5XxOYqIGNPMGBOkgd6ZPbHOOQ/q7iAV7IqC",
        is_admin=False,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient, admin_user):
    """Faz login e retorna headers com token de autenticação."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@test.com", "password": "Admin@123"},
    )
    if response.status_code == 200:
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    return {}


@pytest.fixture
def sample_bot_data():
    """Dados de exemplo para criação de bot."""
    return {
        "name": "Bot Test",
        "description": "Bot de teste automatizado",
        "welcome_message": "Olá! 🌸 Sou a Flora, como posso ajudar?",
        "personality": "friendly",
    }


@pytest.fixture
def sample_license_data():
    """Dados de exemplo para criação de licença."""
    return {
        "plan_id": "plan-basic",
        "client_id": "client-test-001",
        "duration_days": 30,
    }


@pytest.fixture
def sample_plan_data():
    """Dados de exemplo para criação de plano."""
    return {
        "name": "Plano Test",
        "slug": "plano-test",
        "description": "Plano de teste",
        "price_monthly": 99.90,
        "price_yearly": 999.90,
        "messages_limit": 10000,
        "bots_limit": 3,
        "llm_enabled": True,
        "support_level": "email",
        "is_active": True,
        "is_public": True,
    }
