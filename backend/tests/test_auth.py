"""
Flora Platform — Authentication Tests
======================================
Testes para registro, login, tokens e gerenciamento de sessao.
"""

import os
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.security import (
    create_access_token,
    create_refresh_token,
    verify_password,
    get_password_hash,
)


# ─── Registro ───────────────────────────────────────────────
@pytest.mark.asyncio
class TestRegister:
    """Testes de registro de usuarios."""

    async def test_register_success(
        self, client: AsyncClient, sample_user_data: dict
    ):
        """Registro com dados validos retorna 201 e cria usuario."""
        response = await client.post(
            "/api/v1/auth/register", json=sample_user_data
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == sample_user_data["email"]
        assert data["name"] == sample_user_data["name"]
        assert "id" in data
        assert "password" not in data
        assert "hashed_password" not in data

    async def test_register_duplicate_email(
        self, client: AsyncClient, db_session: AsyncSession, sample_user_data: dict
    ):
        """Registro com email duplicado retorna 409."""
        # First registration succeeds
        from backend.schemas.user import UserCreate
        from backend.core.security import get_password_hash

        from backend.models.user import User
        import uuid

        user = User(
            id=str(uuid.uuid4()),
            email=sample_user_data["email"],
            name=sample_user_data["name"],
            hashed_password=get_password_hash(sample_user_data["password"]),
            role="user",
        )
        db_session.add(user)
        await db_session.flush()

        # Second registration should fail
        response = await client.post(
            "/api/v1/auth/register", json=sample_user_data
        )
        assert response.status_code == 409

    async def test_register_weak_password(self, client: AsyncClient):
        """Registro com senha fraca retorna 422."""
        weak_data = {
            "email": "weak@flora.local",
            "password": "123",
            "name": "Weak User",
        }
        response = await client.post("/api/v1/auth/register", json=weak_data)
        assert response.status_code == 422


# ─── Login ──────────────────────────────────────────────────
@pytest.mark.asyncio
class TestLogin:
    """Testes de autenticacao (login/logout)."""

    async def test_login_success(
        self, client: AsyncClient, db_session: AsyncSession, sample_user_data: dict
    ):
        """Login com credenciais validas retorna tokens."""
        # Create user directly in DB
        from backend.models.user import User
        import uuid

        user = User(
            id=str(uuid.uuid4()),
            email=sample_user_data["email"],
            name=sample_user_data["name"],
            hashed_password=get_password_hash(sample_user_data["password"]),
            role="user",
        )
        db_session.add(user)
        await db_session.flush()

        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": sample_user_data["email"],
                "password": sample_user_data["password"],
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_wrong_password(
        self, client: AsyncClient, db_session: AsyncSession, sample_user_data: dict
    ):
        """Login com senha errada retorna 401."""
        from backend.models.user import User
        import uuid

        user = User(
            id=str(uuid.uuid4()),
            email=sample_user_data["email"],
            name=sample_user_data["name"],
            hashed_password=get_password_hash(sample_user_data["password"]),
            role="user",
        )
        db_session.add(user)
        await db_session.flush()

        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": sample_user_data["email"],
                "password": "WrongPassword123!",
            },
        )
        assert response.status_code == 401

    async def test_login_nonexistent_user(self, client: AsyncClient, db_session: AsyncSession):
        """Login com usuario inexistente retorna 401."""
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": "nobody@nowhere.local",
                "password": "Whatever123!",
            },
        )
        assert response.status_code == 401


# ─── User Profile ───────────────────────────────────────────
@pytest.mark.asyncio
class TestUserProfile:
    """Testes de perfil do usuario autenticado."""

    async def test_get_current_user(
        self, client: AsyncClient, db_session: AsyncSession, sample_user_data: dict
    ):
        """GET /auth/me com token valido retorna dados do usuario."""
        from backend.models.user import User
        import uuid

        user = User(
            id=str(uuid.uuid4()),
            email=sample_user_data["email"],
            name=sample_user_data["name"],
            hashed_password=get_password_hash(sample_user_data["password"]),
            role="user",
        )
        db_session.add(user)
        await db_session.flush()

        token = create_access_token(user.id, role=user.role)
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == sample_user_data["email"]
        assert data["id"] == user.id


# ─── Token Refresh ──────────────────────────────────────────
@pytest.mark.asyncio
class TestTokenRefresh:
    """Testes de renovacao de tokens."""

    async def _create_user(self, db_session, **kwargs):
        """Helper: cria usuario no banco de testes."""
        from backend.models.user import User
        import uuid

        defaults = {
            "id": str(uuid.uuid4()),
            "email": "test@flora.local",
            "name": "Test User",
            "hashed_password": get_password_hash("SecurePass123!"),
            "role": "user",
        }
        defaults.update(kwargs)
        user = User(**defaults)
        db_session.add(user)
        await db_session.flush()
        return user

    async def test_token_refresh(self, client: AsyncClient, db_session: AsyncSession):
        """Refresh token valido gera novo access token."""
        user = await self._create_user(db_session)
        old_refresh = create_refresh_token(user.id)

        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": old_refresh},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data


# ─── Logout ─────────────────────────────────────────────────
@pytest.mark.asyncio
class TestLogout:
    """Testes de logout."""

    async def test_logout(self, client: AsyncClient, db_session: AsyncSession):
        """Logout com token valido revoga o token."""
        from backend.models.user import User
        import uuid

        user = User(
            id=str(uuid.uuid4()),
            email="logout@flora.local",
            name="Logout User",
            hashed_password=get_password_hash("SecurePass123!"),
            role="user",
        )
        db_session.add(user)
        await db_session.flush()

        token = create_access_token(user.id, role=user.role)
        response = await client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
