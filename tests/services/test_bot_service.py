"""Testes do Bot Service."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from backend.services.bot_service import BotService


@pytest.fixture
def mock_db():
    return AsyncMock()


@pytest.fixture
def bot_service(mock_db):
    return BotService(db=mock_db)


@pytest.mark.asyncio
async def test_create_bot(bot_service, mock_db):
    """Deve criar novo bot."""
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()

    bot = await bot_service.create_bot(
        name="Bot Test",
        description="Bot de teste",
        owner_id="user-123",
        plan_id="plan-basic",
    )
    # Não deve lançar exceção


@pytest.mark.asyncio
async def test_get_bot(bot_service, mock_db):
    """Deve obter bot por ID."""
    mock_db.execute = AsyncMock()
    bot = await bot_service.get_bot(bot_id="bot-123")
    # Não deve lançar exceção


@pytest.mark.asyncio
async def test_list_bots(bot_service, mock_db):
    """Deve listar bots de um usuário."""
    mock_db.execute = AsyncMock()
    bots = await bot_service.list_bots(user_id="user-123")
    # Não deve lançar exceção


@pytest.mark.asyncio
async def test_update_bot(bot_service, mock_db):
    """Deve atualizar bot."""
    mock_db.commit = AsyncMock()
    bot = await bot_service.update_bot(
        bot_id="bot-123",
        data={"name": "Nome Atualizado"},
    )
    # Não deve lançar exceção


@pytest.mark.asyncio
async def test_delete_bot(bot_service, mock_db):
    """Deve deletar bot."""
    mock_db.commit = AsyncMock()
    result = await bot_service.delete_bot(bot_id="bot-123")
    # Não deve lançar exceção


@pytest.mark.asyncio
async def test_get_bot_stats(bot_service, mock_db):
    """Deve obter estatísticas do bot."""
    mock_db.execute = AsyncMock()
    stats = await bot_service.get_stats(bot_id="bot-123")
    # Não deve lançar exceção
