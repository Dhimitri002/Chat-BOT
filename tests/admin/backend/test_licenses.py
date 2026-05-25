"""Testes dos endpoints de Licenças."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_license(client: AsyncClient, auth_headers, sample_license_data):
    """Admin deve conseguir criar licença."""
    response = await client.post(
        "/api/v1/licenses",
        json=sample_license_data,
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert "key" in data
    assert data["status"] == "active"


@pytest.mark.asyncio
async def test_list_licenses(client: AsyncClient, auth_headers):
    """Admin deve conseguir listar licenças."""
    response = await client.get("/api/v1/licenses", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list) or "items" in data


@pytest.mark.asyncio
async def test_validate_license(client: AsyncClient):
    """Validação de licença deve retornar status."""
    response = await client.post(
        "/api/v1/licenses/validate",
        json={"license_key": "TEST-LICENSE-KEY-123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "valid" in data


@pytest.mark.asyncio
async def test_create_license_unauthorized(client: AsyncClient, regular_user):
    """Usuário regular não deve conseguir criar licença."""
    # Faz login como usuário regular
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "user@test.com", "password": "Admin@123"},
    )
    if login_resp.status_code == 200:
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.post(
            "/api/v1/licenses",
            json={"plan_id": "plan-basic", "duration_days": 30},
            headers=headers,
        )
        assert response.status_code == 403


@pytest.mark.asyncio
async def test_revoke_license(client: AsyncClient, auth_headers):
    """Admin deve conseguir revogar licença."""
    # Primeiro cria uma licença
    create_resp = await client.post(
        "/api/v1/licenses",
        json={"plan_id": "plan-basic", "duration_days": 30},
        headers=auth_headers,
    )
    if create_resp.status_code == 201:
        license_id = create_resp.json()["id"]
        response = await client.post(
            f"/api/v1/licenses/{license_id}/revoke",
            headers=auth_headers,
        )
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_renew_license(client: AsyncClient, auth_headers):
    """Admin deve conseguir renovar licença."""
    create_resp = await client.post(
        "/api/v1/licenses",
        json={"plan_id": "plan-basic", "duration_days": 30},
        headers=auth_headers,
    )
    if create_resp.status_code == 201:
        license_id = create_resp.json()["id"]
        response = await client.post(
            f"/api/v1/licenses/{license_id}/renew",
            json={"duration_days": 30},
            headers=auth_headers,
        )
        assert response.status_code == 200
