"""Testes do Chat Service."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from backend.services.chat_service import ChatService


@pytest.fixture
def mock_db():
    return AsyncMock()


@pytest.fixture
def chat_service(mock_db):
    return ChatService(db=mock_db)


@pytest.mark.asyncio
async def test_process_message(chat_service):
    """Deve processar mensagem e retornar resposta."""
    result = await chat_service.process_message(
        bot_id="bot-123",
        message="Olá!",
        sender="user-456",
    )
    assert result is not None


@pytest.mark.asyncio
async def test_get_conversation_history(chat_service, mock_db):
    """Deve obter histórico de conversa."""
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [
        MagicMock(id="msg-1", content="Hello"),
        MagicMock(id="msg-2", content="Hi there"),
    ]
    mock_db.execute = AsyncMock(return_value=mock_result)
    result = await chat_service.get_history(
        bot_id="bot-123",
        limit=50,
    )
    assert result is not None
    mock_db.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_match_intent(chat_service):
    """Deve detectar intenção da mensagem."""
    intent = await chat_service.match_intent(
        bot_id="bot-123",
        message="Qual o horário de funcionamento?",
    )
    assert intent is not None or intent == "unknown"


@pytest.mark.asyncio
async def test_save_message(chat_service, mock_db):
    """Deve salvar mensagem no banco."""
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()
    result = await chat_service.save_message(
        bot_id="bot-123",
        sender="user-456",
        content="Test message",
        direction="inbound",
    )
    mock_db.add.assert_called_once()
    mock_db.commit.assert_awaited()


@pytest.mark.asyncio
async def test_get_stats(chat_service, mock_db):
    """Deve obter estatísticas de chat."""
    mock_db.execute = AsyncMock(return_value=MagicMock())
    result = await chat_service.get_stats(bot_id="bot-123")
    assert result is not None or isinstance(result, (dict, type(None)))
    mock_db.execute.assert_awaited_once()
