"""Testes do endpoint de Health Check."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Health check deve retornar 200 com status ok."""
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "database" in data


@pytest.mark.asyncio
async def test_health_detailed(client: AsyncClient):
    """Health check detalhado deve incluir métricas."""
    response = await client.get("/api/v1/health?detailed=true")
    assert response.status_code == 200
    data = response.json()
    assert "uptime" in data
    assert "memory" in data
    assert "database" in data
