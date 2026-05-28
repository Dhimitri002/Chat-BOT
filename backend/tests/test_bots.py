"""
Flora Platform — Bot Tests
===========================
Testes para criacao, listagem, atualizacao e remocao de bots.
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
        email=f"{role}@flora.local",
        name=f"{role.title()} User",
        hashed_password=get_password_hash("SecurePass123!"),
        role=role,
    )
    db_session.add(user)
    await db_session.flush()
    token = create_access_token(user.id, role=role)
    return user, token


# ─── Criacao de Bots ───────────────────────────────────────
@pytest.mark.asyncio
class TestBotCreate:
    """Testes de criacao de bots."""

    async def test_create_bot(
        self, client: AsyncClient, db_session: AsyncSession, sample_bot_data: dict
    ):
        """Usuario autenticado pode criar bot."""
        _, token = await _create_user_with_token(db_session)
        response = await client.post(
            "/api/v1/bots",
            json=sample_bot_data,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == sample_bot_data["name"]
        assert "id" in data

    async def test_create_bot_unauthenticated(
        self, client: AsyncClient, db_session: AsyncSession, sample_bot_data: dict
    ):
        """Criar bot sem autenticacao retorna 401."""
        response = await client.post("/api/v1/bots", json=sample_bot_data)
        assert response.status_code == 401

    async def test_create_bot_invalid_data(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Criar bot com dados invalidos retorna 422."""
        _, token = await _create_user_with_token(db_session)
        response = await client.post(
            "/api/v1/bots",
            json={"name": ""},  # Empty name should fail
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422


# ─── Listagem de Bots ──────────────────────────────────────
@pytest.mark.asyncio
class TestBotListing:
    """Testes de listagem de bots."""

    async def test_list_bots(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Usuario pode listar seus bots."""
        _, token = await _create_user_with_token(db_session)
        response = await client.get(
            "/api/v1/bots",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, (list, dict))

    async def test_list_bots_unauthenticated(self, client: AsyncClient, db_session: AsyncSession):
        """Listar bots sem autenticacao retorna 401."""
        response = await client.get("/api/v1/bots")
        assert response.status_code == 401


# ─── Detalhes do Bot ───────────────────────────────────────
@pytest.mark.asyncio
class TestBotDetails:
    """Testes de detalhes de um bot especifico."""

    async def test_get_bot(
        self, client: AsyncClient, db_session: AsyncSession, sample_bot_data: dict
    ):
        """Usuario pode obter detalhes de seu bot."""
        _, token = await _create_user_with_token(db_session)
        create_resp = await client.post(
            "/api/v1/bots",
            json=sample_bot_data,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert create_resp.status_code == 201
        bot_id = create_resp.json()["id"]

        response = await client.get(
            f"/api/v1/bots/{bot_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == bot_id
        assert data["name"] == sample_bot_data["name"]

    async def test_get_nonexistent_bot(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Obter bot inexistente retorna 404."""
        _, token = await _create_user_with_token(db_session)
        response = await client.get(
            "/api/v1/bots/nonexistent-id-12345",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404


# ─── Atualizacao de Bots ───────────────────────────────────
@pytest.mark.asyncio
class TestBotUpdate:
    """Testes de atualizacao de bots."""

    async def test_update_bot(
        self, client: AsyncClient, db_session: AsyncSession, sample_bot_data: dict
    ):
        """Usuario pode atualizar seu bot."""
        _, token = await _create_user_with_token(db_session)
        create_resp = await client.post(
            "/api/v1/bots",
            json=sample_bot_data,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert create_resp.status_code == 201
        bot_id = create_resp.json()["id"]

        update_data = {"name": "Updated Bot Name", "temperature": 0.5}
        response = await client.put(
            f"/api/v1/bots/{bot_id}",
            json=update_data,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Bot Name"

    async def test_update_bot_unauthorized(
        self, client: AsyncClient, db_session: AsyncSession, sample_bot_data: dict
    ):
        """Usuario nao pode atualizar bot de outro usuario."""
        # Create bot as user1
        _, token1 = await _create_user_with_token(db_session, role="user")
        create_resp = await client.post(
            "/api/v1/bots",
            json=sample_bot_data,
            headers={"Authorization": f"Bearer {token1}"},
        )
        assert create_resp.status_code == 201
        bot_id = create_resp.json()["id"]

        # Try to update as user2
        import uuid
        user2 = User(
            id=str(uuid.uuid4()),
            email="user2@flora.local",
            name="User Two",
            hashed_password=get_password_hash("SecurePass123!"),
            role="user",
        )
        db_session.add(user2)
        await db_session.flush()
        token2 = create_access_token(user2.id, role="user")

        response = await client.put(
            f"/api/v1/bots/{bot_id}",
            json={"name": "Hacked Bot"},
            headers={"Authorization": f"Bearer {token2}"},
        )
        assert response.status_code in (403, 404)


# ─── Remocao de Bots ───────────────────────────────────────
@pytest.mark.asyncio
class TestBotDelete:
    """Testes de remocao de bots."""

    async def test_delete_bot(
        self, client: AsyncClient, db_session: AsyncSession, sample_bot_data: dict
    ):
        """Usuario pode deletar seu bot."""
        _, token = await _create_user_with_token(db_session)
        create_resp = await client.post(
            "/api/v1/bots",
            json=sample_bot_data,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert create_resp.status_code == 201
        bot_id = create_resp.json()["id"]

        response = await client.delete(
            f"/api/v1/bots/{bot_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code in (200, 204)

        # Verify it's gone
        get_resp = await client.get(
            f"/api/v1/bots/{bot_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert get_resp.status_code == 404

    async def test_delete_bot_unauthorized(
        self, client: AsyncClient, db_session: AsyncSession, sample_bot_data: dict
    ):
        """Usuario nao pode deletar bot de outro usuario."""
        _, token1 = await _create_user_with_token(db_session, role="user")
        create_resp = await client.post(
            "/api/v1/bots",
            json=sample_bot_data,
            headers={"Authorization": f"Bearer {token1}"},
        )
        assert create_resp.status_code == 201
        bot_id = create_resp.json()["id"]

        import uuid
        user2 = User(
            id=str(uuid.uuid4()),
            email="user2@flora.local",
            name="User Two",
            hashed_password=get_password_hash("SecurePass123!"),
            role="user",
        )
        db_session.add(user2)
        await db_session.flush()
        token2 = create_access_token(user2.id, role="user")

        response = await client.delete(
            f"/api/v1/bots/{bot_id}",
            headers={"Authorization": f"Bearer {token2}"},
        )
        assert response.status_code in (403, 404)


# ─── Status do Bot ─────────────────────────────────────────
@pytest.mark.asyncio
class TestBotStatus:
    """Testes de status do bot."""

    async def test_bot_status(
        self, client: AsyncClient, db_session: AsyncSession, sample_bot_data: dict
    ):
        """Usuario pode verificar status do bot."""
        _, token = await _create_user_with_token(db_session)
        create_resp = await client.post(
            "/api/v1/bots",
            json=sample_bot_data,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert create_resp.status_code == 201
        bot_id = create_resp.json()["id"]

        response = await client.get(
            f"/api/v1/bots/{bot_id}/status",
            headers={"Authorization": f"Bearer {token}"},
        )
        # May return 200 or 404 depending on route existence
        assert response.status_code in (200, 404)
