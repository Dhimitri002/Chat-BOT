"""Testes dos endpoints de WhatsApp."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_whatsapp_status(client: AsyncClient, auth_headers):
    """Deve conseguir obter status do WhatsApp."""
    response = await client.get(
        "/api/v1/whatsapp/status",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "connected" in data


@pytest.mark.asyncio
async def test_whatsapp_connect(client: AsyncClient, auth_headers, sample_bot_data):
    """Deve conseguir iniciar conexão WhatsApp."""
    create_resp = await client.post(
        "/api/v1/bots",
        json=sample_bot_data,
        headers=auth_headers,
    )
    if create_resp.status_code == 201:
        bot_id = create_resp.json()["id"]
        response = await client.post(
            "/api/v1/whatsapp/connect",
            json={"bot_id": bot_id},
            headers=auth_headers,
        )
        assert response.status_code in [200, 202]
        data = response.json()
        assert "status" in data


@pytest.mark.asyncio
async def test_whatsapp_disconnect(client: AsyncClient, auth_headers):
    """Deve conseguir desconectar WhatsApp."""
    response = await client.post(
        "/api/v1/whatsapp/disconnect",
        headers=auth_headers,
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_whatsapp_qr(client: AsyncClient, auth_headers):
    """Deve conseguir obter QR code."""
    response = await client.get(
        "/api/v1/whatsapp/qr",
        headers=auth_headers,
    )
    assert response.status_code in [200, 404]


@pytest.mark.asyncio
async def test_whatsapp_unauthorized(client: AsyncClient):
    """Acesso sem token deve retornar 401."""
    response = await client.get("/api/v1/whatsapp/status")
    assert response.status_code == 401
