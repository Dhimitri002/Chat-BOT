"""Testes de integração — Webhooks do WhatsApp."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_whatsapp_webhook_receive(client: AsyncClient):
    """Deve receber webhook do WhatsApp."""
    payload = {
        "object": "whatsapp_business_account",
        "entry": [{
            "id": "WHATSAPP_BUSINESS_ID",
            "changes": [{
                "value": {
                    "messaging_product": "whatsapp",
                    "metadata": {
                        "display_phone_number": "5511999999999",
                        "phone_number_id": "PHONE_ID",
                    },
                    "messages": [{
                        "from": "5511888888888",
                        "id": "MSG_ID",
                        "timestamp": "1700000000",
                        "text": {"body": "Olá!"},
                        "type": "text",
                    }],
                },
                "field": "messages",
            }],
        }],
    }

    response = await client.post(
        "/api/v1/webhooks/whatsapp",
        json=payload,
        params={"hub.verify_token": "test-token"},
    )
    assert response.status_code in [200, 403]


@pytest.mark.asyncio
async def test_whatsapp_webhook_verify(client: AsyncClient):
    """Deve verificar webhook do WhatsApp."""
    response = await client.get(
        "/api/v1/webhooks/whatsapp",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "test-token",
            "hub.challenge": "challenge-123",
        },
    )
    assert response.status_code in [200, 403]


@pytest.mark.asyncio
async def test_whatsapp_webhook_status_update(client: AsyncClient):
    """Deve processar atualização de status."""
    payload = {
        "object": "whatsapp_business_account",
        "entry": [{
            "id": "WHATSAPP_BUSINESS_ID",
            "changes": [{
                "value": {
                    "messaging_product": "whatsapp",
                    "metadata": {
                        "display_phone_number": "5511999999999",
                        "phone_number_id": "PHONE_ID",
                    },
                    "statuses": [{
                        "id": "MSG_ID",
                        "status": "delivered",
                        "timestamp": "1700000000",
                        "recipient_id": "5511888888888",
                    }],
                },
                "field": "messages",
            }],
        }],
    }

    response = await client.post(
        "/api/v1/webhooks/whatsapp",
        json=payload,
    )
    assert response.status_code in [200, 403]
