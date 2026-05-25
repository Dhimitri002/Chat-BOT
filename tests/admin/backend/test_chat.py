"""Testes dos endpoints de Chat."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_send_message(client: AsyncClient, auth_headers, sample_bot_data):
    """Deve conseguir enviar mensagem para um bot."""
    create_resp = await client.post(
        "/api/v1/bots",
        json=sample_bot_data,
        headers=auth_headers,
    )
    if create_resp.status_code == 201:
        bot_id = create_resp.json()["id"]
        response = await client.post(
            "/api/v1/chat/send",
            json={
                "bot_id": bot_id,
                "message": "Olá, tudo bem?",
                "sender": "test_user",
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "response" in data


@pytest.mark.asyncio
async def test_chat_history(client: AsyncClient, auth_headers):
    """Deve conseguir obter histórico de chat."""
    response = await client.get(
        "/api/v1/chat/history",
        headers=auth_headers,
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_chat_history_by_bot(client: AsyncClient, auth_headers, sample_bot_data):
    """Deve conseguir obter histórico de chat por bot."""
    create_resp = await client.post(
        "/api/v1/bots",
        json=sample_bot_data,
        headers=auth_headers,
    )
    if create_resp.status_code == 201:
        bot_id = create_resp.json()["id"]
        response = await client.get(
            f"/api/v1/chat/history?bot_id={bot_id}",
            headers=auth_headers,
        )
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_chat_unauthorized(client: AsyncClient):
    """Acesso sem token deve retornar 401."""
    response = await client.get("/api/v1/chat/history")
    assert response.status_code == 401
