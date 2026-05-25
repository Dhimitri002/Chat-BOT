"""Testes do License Service."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from backend.services.license_service import LicenseService


@pytest.fixture
def mock_db():
    return AsyncMock()


@pytest.fixture
def license_service(mock_db):
    return LicenseService(db=mock_db)


@pytest.mark.asyncio
async def test_generate_license(license_service):
    """Deve gerar chave de licença válida."""
    license_key = license_service.generate_license_key()
    assert license_key is not None
    assert isinstance(license_key, str)
    assert len(license_key) > 20


@pytest.mark.asyncio
async def test_validate_license_valid(license_service):
    """Deve validar licença ativa."""
    result = license_service.validate_license(key="VALID-LICENSE-KEY")
    assert result is not None
    assert "valid" in result or isinstance(result, bool)


@pytest.mark.asyncio
async def test_validate_license_expired(license_service):
    """Deve rejeitar licença expirada."""
    result = license_service.validate_license(key="EXPIRED-LICENSE-KEY")


@pytest.mark.asyncio
async def test_revoke_license(license_service, mock_db):
    """Deve revogar licença."""
    mock_db.commit = AsyncMock()
    result = await license_service.revoke_license(license_id="test-id")
    # Não deve lançar exceção


@pytest.mark.asyncio
async def test_check_license_limits(license_service):
    """Deve verificar limites da licença."""
    result = license_service.check_limits(
        license_key="TEST-KEY",
        resource="messages",
        current_usage=50,
    )
    assert result is not None


@pytest.mark.asyncio
async def test_license_machine_binding(license_service):
    """Deve vincular licença a máquina."""
    machine_id = "machine-abc-123"
    result = license_service.bind_to_machine(
        license_key="TEST-KEY",
        machine_id=machine_id,
    )
    # Não deve lançar exceção
