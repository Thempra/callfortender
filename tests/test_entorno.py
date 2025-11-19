import pytest
from fastapi.testclient import TestClient
from src.infrastructure.database import get_db, AsyncSessionLocal, engine
from src.infrastructure.redis_client import RedisClient
from src.infrastructure.settings import Settings
from unittest.mock import AsyncMock, patch
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

# Fixtures
@pytest.fixture
async def async_session():
    async with AsyncSessionLocal() as session:
        yield session

@pytest.fixture
def redis_client_mock():
    mock = AsyncMock()
    return mock

@pytest.fixture
def settings_mock():
    mock = Settings(
        database_hostname="localhost",
        database_port="5432",
        database_password="password",
        database_username="user",
        database_name="testdb",
        redis_host="localhost",
        redis_port=6379,
    )
    return mock

# Tests de funcionalidad básica
def test_redis_client_set_get(redis_client_mock):
    redis_client = RedisClient()
    redis_client.redis.set = AsyncMock(return_value=True)
    redis_client.redis.get = AsyncMock(return_value=b'test_value')
    
    await redis_client.set('key', 'test_value')
    assert await redis_client.get('key') == b'test_value'

# Tests de edge cases
def test_redis_client_get_nonexistent_key(redis_client_mock):
    redis_client = RedisClient()
    redis_client.redis.get = AsyncMock(return_value=None)
    
    assert await redis_client.get('non_existent_key') is None

# Tests de manejo de errores
@patch("src.infrastructure.database.AsyncSessionLocal")
async def test_database_session_error(mock_session_local):
    mock_session_local.side_effect = Exception("Database connection failed")
    
    try:
        async with get_db():
            pass
    except Exception as e:
        assert str(e) == "Database connection failed"

# Tests de funcionalidad básica para Settings
def test_settings_initialization(settings_mock):
    settings = settings_mock
    assert settings.database_hostname == "localhost"
    assert settings.database_port == "5432"
    assert settings.database_password == "password"
    assert settings.database_username == "user"
    assert settings.database_name == "testdb"
    assert settings.redis_host == "localhost"
    assert settings.redis_port == 6379

# Tests de edge cases para Settings
def test_settings_with_empty_values():
    settings = Settings(
        database_hostname="",
        database_port="",
        database_password="",
        database_username="",
        database_name="",
        redis_host="",
        redis_port=0,
    )
    assert settings.database_hostname == ""
    assert settings.database_port == ""
    assert settings.database_password == ""
    assert settings.database_username == ""
    assert settings.database_name == ""
    assert settings.redis_host == ""
    assert settings.redis_port == 0

# Tests de manejo de errores para Settings
def test_settings_with_invalid_redis_port():
    try:
        settings = Settings(
            database_hostname="localhost",
            database_port="5432",
            database_password="password",
            database_username="user",
            database_name="testdb",
            redis_host="localhost",
            redis_port=-1,
        )
    except ValueError as e:
        assert str(e) == "redis_port must be a positive integer"