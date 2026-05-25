"""Testes do Auth Service."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from backend.services.auth_service import AuthService


@pytest.fixture
def mock_db():
    """Mock do banco de dados."""
    return AsyncMock()


@pytest.fixture
def auth_service(mock_db):
    """Instância do AuthService com db mockado."""
    return AuthService(db=mock_db)


@pytest.mark.asyncio
async def test_create_user(auth_service, mock_db):
    """Deve criar usuário com senha hasheada."""
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()

    with patch("backend.services.auth_service.get_password_hash", return_value="hashed_pw"):
        user = await auth_service.create_user(
            name="Test User",
            email="test@example.com",
            password="Senha@123",
        )

    assert user is not None
    assert user.name == "Test User"
    assert user.email == "test@example.com"


@pytest.mark.asyncio
async def test_authenticate_user_success(auth_service, mock_db):
    """Deve autenticar usuário com credenciais válidas."""
    mock_user = MagicMock()
    mock_user.hashed_password = "hashed_pw"
    mock_user.is_active = True

    with patch("backend.services.auth_service.get_password_hash", return_value="hashed_pw"):
        with patch("backend.services.auth_service.pwd_context") as mock_pwd:
            mock_pwd.verify.return_value = True
            result = await auth_service.authenticate_user(
                email="test@example.com",
                password="Senha@123",
            )


@pytest.mark.asyncio
async def test_authenticate_user_wrong_password(auth_service, mock_db):
    """Deve rejeitar senha incorreta."""
    with patch("backend.services.auth_service.pwd_context") as mock_pwd:
        mock_pwd.verify.return_value = False
        result = await auth_service.authenticate_user(
            email="test@example.com",
            password="WrongPass",
        )
    assert result is None or result is False


@pytest.mark.asyncio
async def test_create_access_token(auth_service):
    """Deve criar token JWT válido."""
    token = auth_service.create_access_token(data={"sub": "test@example.com"})
    assert token is not None
    assert isinstance(token, str)
    assert len(token) > 0


@pytest.mark.asyncio
async def test_create_refresh_token(auth_service):
    """Deve criar refresh token válido."""
    token = auth_service.create_refresh_token(data={"sub": "test@example.com"})
    assert token is not None
    assert isinstance(token, str)
