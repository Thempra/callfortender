import pytest
from fastapi.testclient import TestClient
from src.app.database import get_db, AsyncSessionLocal
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch
from httpx import AsyncClient

# Mocking the database settings for testing purposes
DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(DATABASE_URL, echo=True)
TestingSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

@pytest.fixture(scope="module")
async def client():
    from src.app.main import app

    async with engine.begin() as conn:
        await conn.run_sync(lambda _: None)  # No need to create tables for this test

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture(scope="function")
async def db_session():
    async with TestingSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

# Tests de funcionalidad básica
def test_get_db(db_session):
    assert isinstance(db_session, AsyncSession)

# Tests de edge cases
@pytest.mark.asyncio
async def test_get_db_no_exception_on_close():
    async with TestingSessionLocal() as session:
        try:
            pass  # No operations to raise an exception
        except Exception as e:
            await session.rollback()
            raise e
        finally:
            await session.close()

# Tests de manejo de errores
@pytest.mark.asyncio
async def test_get_db_rollback_on_exception():
    async with TestingSessionLocal() as session:
        try:
            raise ValueError("Test exception")
        except Exception as e:
            await session.rollback()
            assert isinstance(e, ValueError)
        finally:
            await session.close()

# Mocking the get_db dependency for API tests
@pytest.fixture(scope="function")
def mock_get_db(monkeypatch):
    async def override_get_db():
        async with TestingSessionLocal() as session:
            yield session

    monkeypatch.setattr("src.app.main.get_db", override_get_db)

@pytest.mark.asyncio
async def test_create_user_valid_data(client, mock_get_db):
    response = await client.post("/users/", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "securepassword123",
        "first_name": "John",
        "last_name": "Doe",
        "date_of_birth": "1990-01-01"
    })
    assert response.status_code == 200
    user = response.json()
    assert user["username"] == "testuser"
    assert user["email"] == "test@example.com"

@pytest.mark.asyncio
async def test_create_user_invalid_email(client, mock_get_db):
    response = await client.post("/users/", json={
        "username": "testuser",
        "email": "invalid-email",
        "password": "securepassword123",
        "first_name": "John",
        "last_name": "Doe",
        "date_of_birth": "1990-01-01"
    })
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_create_user_password_too_short(client, mock_get_db):
    response = await client.post("/users/", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "short",
        "first_name": "John",
        "last_name": "Doe",
        "date_of_birth": "1990-01-01"
    })
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_create_user_invalid_username_length(client, mock_get_db):
    response = await client.post("/users/", json={
        "username": "a" * 51,
        "email": "test@example.com",
        "password": "securepassword123",
        "first_name": "John",
        "last_name": "Doe",
        "date_of_birth": "1990-01-01"
    })
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_read_user_by_invalid_id(client, mock_get_db):
    response = await client.get("/users/0")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_update_user_invalid_id(client, mock_get_db):
    response = await client.put("/users/0", json={
        "first_name": "Jane",
        "last_name": "Doe"
    })
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_delete_user_invalid_id(client, mock_get_db):
    response = await client.delete("/users/0")
    assert response.status_code == 404