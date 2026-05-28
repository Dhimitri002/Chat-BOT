"""Testes do Billing Service."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from backend.services.billing_service import BillingService
from fastapi import HTTPException


@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    return db


@pytest.fixture
def mock_plan():
    plan = MagicMock()
    plan.id = "plan-basic"
    plan.name = "Basic"
    plan.max_bots = 3
    plan.max_messages = 1000
    return plan


@pytest.mark.asyncio
async def test_create_subscription_plan_not_found(mock_db):
    """Deve retornar 404 se plano não existir."""
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute = AsyncMock(return_value=mock_result)

    with pytest.raises(HTTPException) as exc_info:
        await BillingService.create_subscription(
            db=mock_db,
            user_id="user-123",
            plan_id="plan-inexistente",
        )
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_create_subscription_success(mock_db, mock_plan):
    """Deve criar nova assinatura com sucesso."""
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_plan
    mock_db.execute = AsyncMock(return_value=mock_result)

    sub = await BillingService.create_subscription(
        db=mock_db,
        user_id="user-123",
        plan_id="plan-basic",
    )
    assert sub is not None
    assert sub.user_id == "user-123"
    assert sub.plan_id == "plan-basic"
    mock_db.add.assert_called_once()
    mock_db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_subscription(mock_db):
    """Deve obter assinatura ativa."""
    expected_sub = MagicMock(id="sub-123", user_id="user-123", status="active")
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = expected_sub
    mock_db.execute = AsyncMock(return_value=mock_result)

    sub = await BillingService.get_active_subscription(db=mock_db, user_id="user-123")
    assert sub is not None
    assert sub.user_id == "user-123"


@pytest.mark.asyncio
async def test_cancel_subscription(mock_db):
    """Deve cancelar assinatura."""
    existing_sub = MagicMock(id="sub-123", status="active")
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = existing_sub
    mock_db.execute = AsyncMock(return_value=mock_result)

    result = await BillingService.cancel_subscription(
        db=mock_db,
        subscription_id="sub-123",
    )
    mock_db.commit.assert_awaited_once()


def test_check_plan_limits_within(mock_plan):
    """Deve retornar True quando uso está dentro do limite."""
    result = BillingService.check_limits(
        plan=mock_plan,
        resource="messages",
        current_usage=500,
    )
    assert result is True


def test_check_plan_limits_exceeded(mock_plan):
    """Deve retornar False quando uso excede o limite."""
    result = BillingService.check_limits(
        plan=mock_plan,
        resource="messages",
        current_usage=2000,
    )
    assert result is False


@pytest.mark.asyncio
async def test_record_usage(mock_db):
    """Deve registrar uso."""
    mock_db.execute = AsyncMock()
    result = await BillingService.record_usage(
        db=mock_db,
        user_id="user-123",
        resource="messages",
        amount=1,
    )
    mock_db.add.assert_called_once()
    mock_db.commit.assert_awaited_once()
