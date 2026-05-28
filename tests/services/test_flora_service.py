"""Testes do Flora AI Service."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from backend.services.flora_service import FloraService


@pytest.fixture
def mock_db():
    return AsyncMock()


@pytest.fixture
def flora_service(mock_db):
    return FloraService(db=mock_db)


@pytest.mark.asyncio
async def test_flora_respond(flora_service):
    """Deve gerar resposta da Flora."""
    response = await flora_service.get_response(
        message="Olá Flora! Como conectar o WhatsApp?",
        session_id="session-123",
    )
    assert response is not None
    assert isinstance(response, str)
    assert len(response) > 0


@pytest.mark.asyncio
async def test_flora_onboarding_guide(flora_service):
    """Deve obter guia de onboarding."""
    guide = await flora_service.get_onboarding_guide()
    assert guide is not None
    assert isinstance(guide, dict) or isinstance(guide, list)


@pytest.mark.asyncio
async def test_flora_help_topic(flora_service):
    """Deve obter ajuda para tópico específico."""
    help_content = await flora_service.get_help(topic="whatsapp")
    assert help_content is not None
    assert isinstance(help_content, str)


@pytest.mark.asyncio
async def test_flora_session_context(flora_service):
    """Deve manter contexto da sessão."""
    context = await flora_service.get_session_context(session_id="session-123")
    assert context is not None or context == {}


@pytest.mark.asyncio
async def test_flora_clear_session(flora_service, mock_db):
    """Deve limpar sessão."""
    mock_db.commit = AsyncMock()
    mock_db.execute = AsyncMock()
    result = await flora_service.clear_session(session_id="session-123")
    mock_db.execute.assert_awaited()
    mock_db.commit.assert_awaited()
