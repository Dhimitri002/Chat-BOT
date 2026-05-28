"""Testes do Bot Service."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from backend.services.bot_service import BotService


@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    return db


@pytest.mark.asyncio
async def test_create_bot(mock_db):
    """Deve criar novo bot."""
    with patch("backend.services.bot_service.uuid4", return_value="test-uuid-123"):
        bot = await BotService.create_bot(
            db=mock_db,
            user_id="user-123",
            data=MagicMock(
                name="Bot Test",
                description="Bot de teste",
                personality="amigável",
                welcome_message=None,
                farewell_message=None,
                config={},
            ),
        )
    assert bot is not None
    assert bot.id == "test-uuid-123"
    assert bot.name == "Bot Test"
    assert bot.owner_id == "user-123"
    mock_db.add.assert_called_once()
    mock_db.commit.assert_awaited_once()
    mock_db.refresh.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_bot(mock_db):
    """Deve obter bot por ID."""
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = MagicMock(id="bot-123", name="Bot Test")
    mock_db.execute = AsyncMock(return_value=mock_result)

    bot = await BotService.get_bot(db=mock_db, bot_id="bot-123")
    assert bot is not None
    assert bot.id == "bot-123"
    mock_db.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_list_bots(mock_db):
    """Deve listar bots de um usuário."""
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [
        MagicMock(id="bot-1", name="Bot 1"),
        MagicMock(id="bot-2", name="Bot 2"),
    ]
    mock_db.execute = AsyncMock(return_value=mock_result)

    bots = await BotService.list_bots(db=mock_db, user_id="user-123")
    assert len(bots) == 2
    assert bots[0].id == "bot-1"
    assert bots[1].id == "bot-2"


@pytest.mark.asyncio
async def test_update_bot(mock_db):
    """Deve atualizar bot."""
    existing_bot = MagicMock(id="bot-123", name="Old Name")
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = existing_bot
    mock_db.execute = AsyncMock(return_value=mock_result)

    updated = await BotService.update_bot(
        db=mock_db,
        bot_id="bot-123",
        user_id="user-123",
        data=MagicMock(name="New Name"),
    )
    assert updated.name == "New Name"
    mock_db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_bot(mock_db):
    """Deve deletar bot."""
    mock_db.execute = AsyncMock()
    result = await BotService.delete_bot(db=mock_db, bot_id="bot-123", user_id="user-123")
    mock_db.execute.assert_awaited()
    mock_db.commit.assert_awaited()


@pytest.mark.asyncio
async def test_get_bot_stats(mock_db):
    """Deve obter estatísticas do bot."""
    mock_db.execute = AsyncMock(return_value=MagicMock())
    stats = await BotService.get_stats(db=mock_db, bot_id="bot-123")
    # get_stats returns a dict
    assert isinstance(stats, dict) or stats is None
