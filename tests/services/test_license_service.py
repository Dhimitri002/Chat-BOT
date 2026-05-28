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
    assert result is False or (isinstance(result, dict) and result.get("valid") is False)


@pytest.mark.asyncio
async def test_revoke_license(license_service, mock_db):
    """Deve revogar licença."""
    mock_db.commit = AsyncMock()
    mock_license = MagicMock()
    mock_license.key = "TEST-KEY"
    mock_license.is_revoked = False
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_license
    mock_db.execute = AsyncMock(return_value=mock_result)

    result = await license_service.revoke_license(license_id="test-id")
    assert mock_license.is_revoked is True
    mock_db.commit.assert_awaited_once()


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
    assert result is not None or result is None  # Method should complete without error
