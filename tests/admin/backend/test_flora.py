"""Testes dos endpoints da Flora AI."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_flora_chat(client: AsyncClient, auth_headers):
    """Deve conseguir enviar mensagem para Flora AI."""
    response = await client.post(
        "/api/v1/flora/chat",
        json={"message": "Olá Flora! Como conectar o WhatsApp?"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert "session_id" in data


@pytest.mark.asyncio
async def test_flora_chat_history(client: AsyncClient, auth_headers):
    """Deve conseguir obter histórico de chat com Flora."""
    response = await client.get(
        "/api/v1/flora/history",
        headers=auth_headers,
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_flora_onboarding(client: AsyncClient, auth_headers):
    """Deve conseguir obter guia de onboarding."""
    response = await client.get(
        "/api/v1/flora/onboarding",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "steps" in data


@pytest.mark.asyncio
async def test_flora_help(client: AsyncClient, auth_headers):
    """Deve conseguir obter ajuda para tópico específico."""
    response = await client.post(
        "/api/v1/flora/help",
        json={"topic": "whatsapp"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "content" in data


@pytest.mark.asyncio
async def test_flora_clear_history(client: AsyncClient, auth_headers):
    """Deve conseguir limpar histórico da Flora."""
    response = await client.delete(
        "/api/v1/flora/history",
        headers=auth_headers,
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_flora_unauthorized(client: AsyncClient):
    """Acesso sem token deve retornar 401."""
    response = await client.post(
        "/api/v1/flora/chat",
        json={"message": "Olá"},
    )
    assert response.status_code == 401
