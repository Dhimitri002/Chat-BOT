"""Testes end-to-end — fluxos completos do sistema."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_complete_user_journey(client: AsyncClient):
    """Jornada completa: registro → login → criar bot → conectar → chat → Flora."""
    # 1. Registro
    reg_resp = await client.post(
        "/api/v1/auth/register",
        json={
            "name": "E2E User",
            "email": "e2e@test.com",
            "password": "Senha@123456",
        },
    )
    assert reg_resp.status_code == 201

    # 2. Login
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "e2e@test.com", "password": "Senha@123456"},
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Verificar perfil
    me_resp = await client.get("/api/v1/auth/me", headers=headers)
    assert me_resp.status_code == 200

    # 4. Listar planos
    plans_resp = await client.get("/api/v1/plans")
    assert plans_resp.status_code == 200

    # 5. Criar bot
    bot_resp = await client.post(
        "/api/v1/bots",
        json={
            "name": "E2E Bot",
            "description": "Bot de teste E2E",
            "welcome_message": "Olá! 🌸",
        },
        headers=headers,
    )
    assert bot_resp.status_code == 201
    bot_id = bot_resp.json()["id"]

    # 6. Obter detalhes do bot
    detail_resp = await client.get(
        f"/api/v1/bots/{bot_id}", headers=headers
    )
    assert detail_resp.status_code == 200

    # 7. Enviar mensagem para Flora
    flora_resp = await client.post(
        "/api/v1/flora/chat",
        json={"message": "Olá Flora!"},
        headers=headers,
    )
    assert flora_resp.status_code == 200

    # 8. Verificar status do WhatsApp
    wa_resp = await client.get(
        "/api/v1/whatsapp/status", headers=headers
    )
    assert wa_resp.status_code == 200

    # 9. Deletar bot
    delete_resp = await client.delete(
        f"/api/v1/bots/{bot_id}", headers=headers
    )
    assert delete_resp.status_code == 200

    # 10. Logout
    logout_resp = await client.post(
        "/api/v1/auth/logout", headers=headers
    )
    assert logout_resp.status_code == 200


@pytest.mark.asyncio
async def test_admin_management_flow(client: AsyncClient, auth_headers):
    """Fluxo de administração: dashboard → licenças → analytics."""
    # 1. Dashboard admin
    dash_resp = await client.get(
        "/api/v1/admin/dashboard", headers=auth_headers
    )
    assert dash_resp.status_code in [200, 403]

    # 2. Listar licenças
    lic_resp = await client.get(
        "/api/v1/licenses", headers=auth_headers
    )
    assert lic_resp.status_code == 200

    # 3. Criar licença
    create_resp = await client.post(
        "/api/v1/licenses",
        json={"plan_id": "plan-basic", "duration_days": 30},
        headers=auth_headers,
    )
    assert create_resp.status_code == 201

    # 4. Analytics
    analytics_resp = await client.get(
        "/api/v1/analytics", headers=auth_headers
    )
    assert analytics_resp.status_code in [200, 403]


@pytest.mark.asyncio
async def test_health_and_readiness(client: AsyncClient):
    """Sistema deve estar saudável."""
    # Health check
    health = await client.get("/api/v1/health")
    assert health.status_code == 200
    data = health.json()
    assert data["status"] == "ok"
