"""
Shared test fixtures and configuration
"""
import pytest
import os
from unittest.mock import MagicMock
import asyncio


@pytest.fixture
def env_vars():
    """Fixture para manipular variáveis de ambiente durante testes"""
    old_env = dict(os.environ)
    yield os.environ
    os.environ.clear()
    os.environ.update(old_env)


@pytest.fixture
def secure_env(env_vars):
    """Fixture com variáveis seguras pré-configuradas"""
    env_vars["SECRET_KEY"] = "4efc5d1234e04803db2cf92f57018de199e4bc5fc21833f8468b38681d468ff5"
    env_vars["FLORA_MASTER_KEY"] = "2a569fa2d90eb9b7ae2203db9af48bd5acd0391ffb90652280ee581ce6c1d40f"
    env_vars["LICENSE_SIGNING_KEY"] = "e1a0bbfdbb29669915d2a13f1d7df5c4d2a63b2989fc9e4c09dcf1a8093f9902"
    return env_vars


@pytest.fixture
def mock_db():
    """Fixture para mock de database session"""
    db = MagicMock()
    db.execute = MagicMock(return_value=MagicMock())
    db.add = MagicMock()
    db.commit = MagicMock()
    db.rollback = MagicMock()
    return db


@pytest.fixture
async def async_mock_db():
    """Fixture para async mock de database session"""
    db = MagicMock()
    
    async def async_execute(query):
        return MagicMock()
    
    db.execute = async_execute
    db.add = MagicMock()
    db.commit = MagicMock()
    db.rollback = MagicMock()
    return db
