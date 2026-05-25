"""Testes dos endpoints de Bots."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_bot(client: AsyncClient, auth_headers, sample_bot_data):
    """Usuário autenticado deve conseguir criar bot."""
    response = await client.post(
        "/api/v1/bots",
        json=sample_bot_data,
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Bot Test"
    assert "id" in data
    assert data["status"] == "inactive"


@pytest.mark.asyncio
async def test_list_bots(client: AsyncClient, auth_headers):
    """Usuário autenticado deve conseguir listar bots."""
    response = await client.get("/api/v1/bots", headers=auth_headers)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_bot_detail(client: AsyncClient, auth_headers, sample_bot_data):
    """Deve conseguir obter detalhes de um bot."""
    create_resp = await client.post(
        "/api/v1/bots",
        json=sample_bot_data,
        headers=auth_headers,
    )
    if create_resp.status_code == 201:
        bot_id = create_resp.json()["id"]
        response = await client.get(f"/api/v1/bots/{bot_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Bot Test"


@pytest.mark.asyncio
async def test_update_bot(client: AsyncClient, auth_headers, sample_bot_data):
    """Deve conseguir atualizar um bot."""
    create_resp = await client.post(
        "/api/v1/bots",
        json=sample_bot_data,
        headers=auth_headers,
    )
    if create_resp.status_code == 201:
        bot_id = create_resp.json()["id"]
        response = await client.put(
            f"/api/v1/bots/{bot_id}",
            json={"name": "Bot Atualizado", "description": "Descrição atualizada"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Bot Atualizado"


@pytest.mark.asyncio
async def test_delete_bot(client: AsyncClient, auth_headers, sample_bot_data):
    """Deve conseguir deletar um bot."""
    create_resp = await client.post(
        "/api/v1/bots",
        json=sample_bot_data,
        headers=auth_headers,
    )
    if create_resp.status_code == 201:
        bot_id = create_resp.json()["id"]
        response = await client.delete(
            f"/api/v1/bots/{bot_id}", headers=auth_headers
        )
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_bot_unauthorized(client: AsyncClient):
    """Acesso sem token deve retornar 401."""
    response = await client.get("/api/v1/bots")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_bot_stats(client: AsyncClient, auth_headers, sample_bot_data):
    """Deve conseguir obter stats de um bot."""
    create_resp = await client.post(
        "/api/v1/bots",
        json=sample_bot_data,
        headers=auth_headers,
    )
    if create_resp.status_code == 201:
        bot_id = create_resp.json()["id"]
        response = await client.get(
            f"/api/v1/bots/{bot_id}/stats", headers=auth_headers
        )
        assert response.status_code == 200
