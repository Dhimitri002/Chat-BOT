"""Testes de integração — fluxos completos da API."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_full_auth_flow(client: AsyncClient):
    """Fluxo completo: registro → login → acesso → logout."""
    # 1. Registro
    register_resp = await client.post(
        "/api/v1/auth/register",
        json={
            "name": "Integration Test",
            "email": "integration@test.com",
            "password": "Senha@123456",
        },
    )
    assert register_resp.status_code == 201

    # 2. Login
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "integration@test.com", "password": "Senha@123456"},
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Acesso a endpoint protegido
    me_resp = await client.get("/api/v1/auth/me", headers=headers)
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == "integration@test.com"

    # 4. Logout
    logout_resp = await client.post("/api/v1/auth/logout", headers=headers)
    assert logout_resp.status_code == 200


@pytest.mark.asyncio
async def test_full_bot_creation_flow(client: AsyncClient, auth_headers):
    """Fluxo completo: criar bot → listar → obter → atualizar → deletar."""
    # 1. Criar
    create_resp = await client.post(
        "/api/v1/bots",
        json={
            "name": "Integration Bot",
            "description": "Bot de integração",
            "welcome_message": "Olá! 🌸",
        },
        headers=auth_headers,
    )
    assert create_resp.status_code == 201
    bot_id = create_resp.json()["id"]

    # 2. Listar
    list_resp = await client.get("/api/v1/bots", headers=auth_headers)
    assert list_resp.status_code == 200

    # 3. Obter detalhes
    detail_resp = await client.get(
        f"/api/v1/bots/{bot_id}", headers=auth_headers
    )
    assert detail_resp.status_code == 200

    # 4. Atualizar
    update_resp = await client.put(
        f"/api/v1/bots/{bot_id}",
        json={"name": "Bot Atualizado"},
        headers=auth_headers,
    )
    assert update_resp.status_code == 200

    # 5. Deletar
    delete_resp = await client.delete(
        f"/api/v1/bots/{bot_id}", headers=auth_headers
    )
    assert delete_resp.status_code == 200


@pytest.mark.asyncio
async def test_flora_chat_flow(client: AsyncClient, auth_headers):
    """Fluxo completo: chat com Flora → histórico → limpar."""
    # 1. Enviar mensagem
    chat_resp = await client.post(
        "/api/v1/flora/chat",
        json={"message": "Olá Flora! Me ajude com o WhatsApp."},
        headers=auth_headers,
    )
    assert chat_resp.status_code == 200
    session_id = chat_resp.json().get("session_id")

    # 2. Obter histórico
    history_resp = await client.get(
        "/api/v1/flora/history",
        headers=auth_headers,
    )
    assert history_resp.status_code == 200

    # 3. Limpar histórico
    clear_resp = await client.delete(
        "/api/v1/flora/history",
        headers=auth_headers,
    )
    assert clear_resp.status_code == 200


@pytest.mark.asyncio
async def test_license_lifecycle_flow(client: AsyncClient, auth_headers):
    """Fluxo completo: criar licença → validar → revogar."""
    # 1. Criar licença
    create_resp = await client.post(
        "/api/v1/licenses",
        json={"plan_id": "plan-basic", "duration_days": 30},
        headers=auth_headers,
    )
    assert create_resp.status_code == 201
    license_id = create_resp.json()["id"]
    license_key = create_resp.json()["key"]

    # 2. Validar licença
    validate_resp = await client.post(
        "/api/v1/licenses/validate",
        json={"license_key": license_key},
    )
    assert validate_resp.status_code == 200

    # 3. Revogar licença
    revoke_resp = await client.post(
        f"/api/v1/licenses/{license_id}/revoke",
        headers=auth_headers,
    )
    assert revoke_resp.status_code == 200
