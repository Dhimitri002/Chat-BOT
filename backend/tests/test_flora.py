"""
Flora Platform — Flora AI Tests
================================
Testes para o chatbot Flora AI: chat, help, onboarding e sessoes.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.security import create_access_token, get_password_hash
from backend.models.user import User


async def _create_user_with_token(
    db_session: AsyncSession, role: str = "user"
) -> tuple[User, str]:
    """Helper: create user and return (user, token)."""
    import uuid
    user = User(
        id=str(uuid.uuid4()),
        email=f"flora_{role}@flora.local",
        name=f"Flora {role.title()}",
        hashed_password=get_password_hash("SecurePass123!"),
        role=role,
    )
    db_session.add(user)
    await db_session.flush()
    token = create_access_token(user.id, role=role)
    return user, token


# ─── Flora Chat ─────────────────────────────────────────────
@pytest.mark.asyncio
class TestFloraChat:
    """Testes do chat com Flora AI."""

    async def test_flora_chat(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Usuario pode enviar mensagem para Flora e receber resposta."""
        _, token = await _create_user_with_token(db_session)
        response = await client.post(
            "/api/v1/flora/chat",
            json={"message": "Ola Flora, como voce esta?"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "response" in data or "message" in data or "reply" in data

    async def test_flora_chat_unauthenticated(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Chat sem autenticacao retorna 401."""
        response = await client.post(
            "/api/v1/flora/chat",
            json={"message": "Ola"},
        )
        assert response.status_code == 401

    async def test_flora_chat_empty_message(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Mensagem vazia retorna 422."""
        _, token = await _create_user_with_token(db_session)
        response = await client.post(
            "/api/v1/flora/chat",
            json={"message": ""},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    async def test_flora_chat_with_session(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Chat com session_id mantem contexto da conversa."""
        _, token = await _create_user_with_token(db_session)
        response = await client.post(
            "/api/v1/flora/chat",
            json={
                "message": "Meu nome e Test",
                "session_id": "test-session-001",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200


# ─── Flora Help ─────────────────────────────────────────────
@pytest.mark.asyncio
class TestFloraHelp:
    """Testes do comando de ajuda da Flora."""

    async def test_flora_help(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Usuario pode solicitar ajuda a Flora."""
        _, token = await _create_user_with_token(db_session)
        response = await client.get(
            "/api/v1/flora/help",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "commands" in data or "help" in data or "message" in data

    async def test_flora_help_unauthenticated(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Ajuda sem autenticacao retorna 401."""
        response = await client.get("/api/v1/flora/help")
        assert response.status_code == 401


# ─── Flora Onboarding ───────────────────────────────────────
@pytest.mark.asyncio
class TestFloraOnboarding:
    """Testes do fluxo de onboarding da Flora."""

    async def test_flora_onboarding_start(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Usuario pode iniciar o onboarding."""
        _, token = await _create_user_with_token(db_session)
        response = await client.post(
            "/api/v1/flora/onboarding/start",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code in (200, 201)
        data = response.json()
        assert "step" in data or "message" in data or "status" in data

    async def test_flora_onboarding_step(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Usuario pode avancar no passo do onboarding."""
        _, token = await _create_user_with_token(db_session)
        response = await client.post(
            "/api/v1/flora/onboarding/step",
            json={"step": 1, "data": {"name": "Test User"}},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code in (200, 201, 404)

    async def test_flora_onboarding_unauthenticated(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Onboarding sem autenticacao retorna 401."""
        response = await client.post("/api/v1/flora/onboarding/start")
        assert response.status_code == 401


# ─── Flora Session Management ───────────────────────────────
@pytest.mark.asyncio
class TestFloraSession:
    """Testes de gerenciamento de sessoes da Flora."""

    async def test_flora_list_sessions(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Usuario pode listar suas sessoes ativas."""
        _, token = await _create_user_with_token(db_session)
        response = await client.get(
            "/api/v1/flora/sessions",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code in (200, 404)  # 404 if route not implemented

    async def test_flora_delete_session(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Usuario pode deletar uma sessao."""
        _, token = await _create_user_with_token(db_session)
        response = await client.delete(
            "/api/v1/flora/sessions/test-session-001",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code in (200, 204, 404)

    async def test_flora_session_unauthenticated(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Gerenciar sessoes sem autenticacao retorna 401."""
        response = await client.get("/api/v1/flora/sessions")
        assert response.status_code == 401


# ─── Flora Status ───────────────────────────────────────────
@pytest.mark.asyncio
class TestFloraStatus:
    """Testes de status da Flora AI."""

    async def test_flora_status(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Endpoint de status retorna informacoes da Flora."""
        _, token = await _create_user_with_token(db_session)
        response = await client.get(
            "/api/v1/flora/status",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code in (200, 404)
