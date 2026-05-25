"""Testes dos endpoints de Autenticação."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_user(client: AsyncClient):
    """Registro de novo usuário deve retornar 201."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "name": "Novo Usuário",
            "email": "novo@test.com",
            "password": "Senha@123456",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "novo@test.com"
    assert "id" in data
    assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    """Registro com email duplicado deve retornar 409."""
    payload = {
        "name": "Usuário Duplicado",
        "email": "dup@test.com",
        "password": "Senha@123456",
    }
    await client.post("/api/v1/auth/register", json=payload)
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_register_weak_password(client: AsyncClient):
    """Registro com senha fraca deve retornar 422."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "name": "Test",
            "email": "weak@test.com",
            "password": "123",
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, admin_user):
    """Login com credenciais válidas deve retornar tokens."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@test.com", "password": "Admin@123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, admin_user):
    """Login com senha errada deve retornar 401."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@test.com", "password": "WrongPassword123"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient):
    """Login com usuário inexistente deve retornar 401."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@test.com", "password": "SomePass123"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user(client: AsyncClient, auth_headers):
    """Endpoint /me deve retornar dados do usuário autenticado."""
    response = await client.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "admin@test.com"


@pytest.mark.asyncio
async def test_get_current_user_no_token(client: AsyncClient):
    """Endpoint /me sem token deve retornar 401."""
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token(client: AsyncClient, admin_user):
    """Refresh token deve gerar novo access token."""
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@test.com", "password": "Admin@123"},
    )
    refresh_token = login_response.json()["refresh_token"]

    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data


@pytest.mark.asyncio
async def test_logout(client: AsyncClient, auth_headers):
    """Logout deve invalidar o token."""
    response = await client.post("/api/v1/auth/logout", headers=auth_headers)
    assert response.status_code == 200
