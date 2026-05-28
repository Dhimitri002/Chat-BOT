"""
Flora Platform — Test Fixtures
================================
Shared fixtures for all test modules.

Uses in-memory SQLite for fast, isolated async testing.
Each test function gets a fresh database session.
"""

import asyncio
import os
import sys
from typing import AsyncGenerator, Generator
from unittest.mock import MagicMock

import pytest
import pytest_asyncio
from asgi_lifespan import LifespanManager
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

# ── Ensure project root is on path ──────────────────────────
# So `import backend.X` works from any directory.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from backend.config import Settings  # noqa: E402
from backend.database import Base  # noqa: E402

# ─── Environment Setup ──────────────────────────────────────
os.environ.setdefault("SECRET_KEY", "test-secret-key-that-is-32-chars!!")
os.environ.setdefault("FLORA_MASTER_KEY", "test-flora-master-key-32-chars!")
os.environ.setdefault(
    "LICENSE_SIGNING_KEY", "test-license-signing-key-32-ch!"
)
os.environ.setdefault("ENCRYPTION_MASTER_KEY", "test-encryption-key-32-bytes!!")
os.environ.setdefault("LICENSE_ENCRYPTION_KEY", "test-license-encryption-key!!")

# Override settings singleton for tests
test_settings = Settings()
test_settings.DATABASE_URL = "sqlite+aiosqlite:///./test_flora.db"

# ─── Test Database Engine ───────────────────────────────────
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_flora.db"
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)


# ─── Event Loop Fixture ─────────────────────────────────────
@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create a new event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ─── Database Fixtures ──────────────────────────────────────
@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Create a fresh in-memory database session for each test.
    Tables are created before the test and dropped after.
    """
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as session:
        yield session
        await session.rollback()

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    try:
        os.remove("./test_flora.db")
    except FileNotFoundError:
        pass


# ─── App Import (lazy to ensure env is set) ─────────────────
def _get_app():
    """Import the FastAPI app after environment is configured."""
    from backend.main import app
    return app


# ─── Async HTTP Client Fixture ──────────────────────────────
@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Async HTTP client for testing API endpoints.
    Overrides the database dependency to use the test session.
    """
    from backend.database import get_db
    from backend.main import app

    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


# ─── Mock DB Fixture ────────────────────────────────────────
@pytest.fixture
def mock_db() -> MagicMock:
    """Synchronous mock database session."""
    db = MagicMock()
    db.execute = MagicMock(return_value=MagicMock())
    db.add = MagicMock()
    db.commit = MagicMock()
    db.rollback = MagicMock()
    return db


@pytest.fixture
def async_mock_db() -> MagicMock:
    """Async mock database session."""
    db = MagicMock()

    async def _async_execute(query):
        return MagicMock()

    db.execute = _async_execute
    db.add = MagicMock()
    db.commit = MagicMock()
    db.rollback = MagicMock()
    return db


# ─── Settings Fixture ───────────────────────────────────────
@pytest.fixture
def settings() -> Settings:
    """Test settings instance."""
    return test_settings


# ─── Test Data Factories ────────────────────────────────────
@pytest.fixture
def sample_user_data() -> dict:
    """Sample user registration data."""
    return {
        "email": "test@flora.local",
        "password": "SecurePass123!",
        "name": "Test User",
    }


@pytest.fixture
def sample_admin_data() -> dict:
    """Sample admin registration data."""
    return {
        "email": "admin@flora.local",
        "password": "AdminPass456!",
        "full_name": "Admin User",
        "role": "admin",
    }


@pytest.fixture
def sample_license_data() -> dict:
    """Sample license creation data."""
    return {
        "plan": "pro",
        "duration_days": 30,
        "customer_name": "Test Customer",
        "customer_email": "customer@example.com",
        "max_bots": 3,
    }


@pytest.fixture
def sample_bot_data() -> dict:
    """Sample bot creation data."""
    return {
        "name": "Test Bot",
        "description": "Bot for testing purposes",
        "personality": "helpful and friendly",
        "response_language": "pt-BR",
        "max_tokens": 1024,
        "temperature": 0.7,
    }
