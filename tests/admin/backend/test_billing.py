"""Testes dos endpoints de Billing/Planos."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_plans(client: AsyncClient):
    """Deve conseguir listar planos públicos."""
    response = await client.get("/api/v1/plans")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list) or "items" in data


@pytest.mark.asyncio
async def test_get_plan_detail(client: AsyncClient):
    """Deve conseguir obter detalhes de um plano."""
    response = await client.get("/api/v1/plans/starter")
    assert response.status_code in [200, 404]


@pytest.mark.asyncio
async def test_create_subscription(client: AsyncClient, auth_headers):
    """Deve conseguir criar assinatura."""
    response = await client.post(
        "/api/v1/billing/subscribe",
        json={"plan_id": "plan-basic", "payment_method": "stripe"},
        headers=auth_headers,
    )
    assert response.status_code in [200, 201]


@pytest.mark.asyncio
async def test_get_subscription(client: AsyncClient, auth_headers):
    """Deve conseguir obter assinatura atual."""
    response = await client.get(
        "/api/v1/billing/subscription",
        headers=auth_headers,
    )
    assert response.status_code in [200, 404]


@pytest.mark.asyncio
async def test_billing_unauthorized(client: AsyncClient):
    """Acesso sem token deve retornar 401."""
    response = await client.get("/api/v1/billing/subscription")
    assert response.status_code == 401
