"""Testes do Billing Service."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from backend.services.billing_service import BillingService


@pytest.fixture
def mock_db():
    return AsyncMock()


@pytest.fixture
def billing_service(mock_db):
    return BillingService(db=mock_db)


@pytest.mark.asyncio
async def test_create_subscription(billing_service, mock_db):
    """Deve criar nova assinatura."""
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()

    sub = await billing_service.create_subscription(
        user_id="user-123",
        plan_id="plan-basic",
        payment_method="stripe",
    )
    # Não deve lançar exceção


@pytest.mark.asyncio
async def test_get_subscription(billing_service, mock_db):
    """Deve obter assinatura ativa."""
    mock_db.execute = AsyncMock()
    sub = await billing_service.get_active_subscription(user_id="user-123")
    # Não deve lançar exceção


@pytest.mark.asyncio
async def test_cancel_subscription(billing_service, mock_db):
    """Deve cancelar assinatura."""
    mock_db.commit = AsyncMock()
    result = await billing_service.cancel_subscription(
        subscription_id="sub-123",
    )
    # Não deve lançar exceção


@pytest.mark.asyncio
async def test_check_plan_limits(billing_service):
    """Deve verificar limites do plano."""
    result = billing_service.check_limits(
        plan_id="plan-basic",
        resource="messages",
        current_usage=500,
    )
    # Não deve lançar exceção


@pytest.mark.asyncio
async def test_record_usage(billing_service, mock_db):
    """Deve registrar uso."""
    mock_db.commit = AsyncMock()
    result = await billing_service.record_usage(
        user_id="user-123",
        resource="messages",
        amount=1,
    )
    # Não deve lançar exceção
