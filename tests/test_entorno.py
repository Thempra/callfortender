import pytest
from fastapi.testclient import TestClient
from src.app.database import get_db, AsyncSessionLocal
from unittest.mock import patch, AsyncMock
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from pydantic import ValidationError
from datetime import date

# Fixtures
@pytest.fixture(scope="module")
def client():
    from fastapi import FastAPI
    from src.app.api.router import router

    app = FastAPI()
    app.include_router(router)
    return TestClient(app)

@pytest.fixture(scope="module")
async def async_session():
    DATABASE_URL = "sqlite+aiosqlite:///:memory:"
    engine = create_async_engine(DATABASE_URL, echo=True)
    AsyncSessionLocal = sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    async with engine.begin() as conn:
        await conn.run_sync(lambda _: None)  # No models to create in memory for this test

    async_session = AsyncSessionLocal()
    try:
        yield async_session
    finally:
        await async_session.close()

@pytest.fixture(scope="module")
def valid_user_data():
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "securepassword123",
        "first_name": "John",
        "last_name": "Doe",
        "date_of_birth": date(1990, 1, 1)
    }

@pytest.fixture(scope="module")
def valid_user_update_data():
    return {
        "first_name": "Jane",
        "last_name": "Smith"
    }

# Tests de funcionalidad básica
def test_create_user_valid_data(client, valid_user_data):
    with patch("src.app.api.router.get_db", new_callable=AsyncMock) as mock_get_db:
        mock_session = AsyncMock()
        mock_get_db.return_value.__aenter__.return_value = mock_session
        response = client.post("/users/", json=valid_user_data)
        assert response.status_code == 200
        user = response.json()
        assert user["username"] == valid_user_data["username"]
        assert user["email"] == valid_user_data["email"]

def test_read_users(client):
    with patch("src.app.api.router.get_db", new_callable=AsyncMock) as mock_get_db:
        mock_session = AsyncMock()
        mock_get_db.return_value.__aenter__.return_value = mock_session
        response = client.get("/users/")
        assert response.status_code == 200

def test_read_user_by_id(client):
    with patch("src.app.api.router.get_db", new_callable=AsyncMock) as mock_get_db:
        mock_session = AsyncMock()
        mock_get_db.return_value.__aenter__.return_value = mock_session
        response = client.get("/users/1")
        assert response.status_code == 200

def test_update_user_valid_data(client, valid_user_update_data):
    with patch("src.app.api.router.get_db", new_callable=AsyncMock) as mock_get_db:
        mock_session = AsyncMock()
        mock_get_db.return_value.__aenter__.return_value = mock_session
        response = client.put("/users/1", json=valid_user_update_data)
        assert response.status_code == 200

def test_delete_user(client):
    with patch("src.app.api.router.get_db", new_callable=AsyncMock) as mock_get_db:
        mock_session = AsyncMock()
        mock_get_db.return_value.__aenter__.return_value = mock_session
        response = client.delete("/users/1")
        assert response.status_code == 200

# Tests de edge cases
def test_create_user_min_length_username(client):
    user_data = {
        "username": "us",
        "email": "test@example.com",
        "password": "securepassword123"
    }
    with patch("src.app.api.router.get_db", new_callable=AsyncMock) as mock_get_db:
        mock_session = AsyncMock()
        mock_get_db.return_value.__aenter__.return_value = mock_session
        response = client.post("/users/", json=user_data)
        assert response.status_code == 422

def test_create_user_max_length_username(client):
    user_data = {
        "username": "a" * 50,
        "email": "test@example.com",
        "password": "securepassword123"
    }
    with patch("src.app.api.router.get_db", new_callable=AsyncMock) as mock_get_db:
        mock_session = AsyncMock()
        mock_get_db.return_value.__aenter__.return_value = mock_session
        response = client.post("/users/", json=user_data)
        assert response.status_code == 200

def test_create_user_no_first_name_or_last_name(client, valid_user_data):
    user_data = {
        "username": valid_user_data["username"],
        "email": valid_user_data["email"],
        "password": valid_user_data["password"]
    }
    with patch("src.app.api.router.get_db", new_callable=AsyncMock) as mock_get_db:
        mock_session = AsyncMock()
        mock_get_db.return_value.__aenter__.return_value = mock_session
        response = client.post("/users/", json=user_data)
        assert response.status_code == 200

def test_create_user_no_date_of_birth(client, valid_user_data):
    user_data = {
        "username": valid_user_data["username"],
        "email": valid_user_data["email"],
        "password": valid_user_data["password"]
    }
    with patch("src.app.api.router.get_db", new_callable=AsyncMock) as mock_get_db:
        mock_session = AsyncMock()
        mock_get_db.return_value.__aenter__.return_value = mock_session
        response = client.post("/users/", json=user_data)
        assert response.status_code == 200

# Tests de manejo de errores
def test_create_user_invalid_email(client):
    user_data = {
        "username": "testuser",
        "email": "invalid-email",
        "password": "securepassword123"
    }
    with patch("src.app.api.router.get_db", new_callable=AsyncMock) as mock_get_db:
        mock_session = AsyncMock()
        mock_get_db.return_value.__aenter__.return_value = mock_session
        response = client.post("/users/", json=user_data)
        assert response.status_code == 422

def test_create_user_password_too_short(client):
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "short"
    }
    with patch("src.app.api.router.get_db", new_callable=AsyncMock) as mock_get_db:
        mock_session = AsyncMock()
        mock_get_db.return_value.__aenter__.return_value = mock_session
        response = client.post("/users/", json=user_data)
        assert response.status_code == 422

def test_create_user_invalid_username_length(client):
    user_data = {
        "username": "a" * 51,
        "email": "test@example.com",
        "password": "securepassword123"
    }
    with patch("src.app.api.router.get_db", new_callable=AsyncMock) as mock_get_db:
        mock_session = AsyncMock()
        mock_get_db.return_value.__aenter__.return_value = mock_session
        response = client.post("/users/", json=user_data)
        assert response.status_code == 422

def test_read_user_by_invalid_id(client):
    with patch("src.app.api.router.get_db", new_callable=AsyncMock) as mock_get_db:
        mock_session = AsyncMock()
        mock_get_db.return_value.__aenter__.return_value = mock_session
        response = client.get("/users/0")
        assert response.status_code == 404

def test_update_user_invalid_id(client, valid_user_update_data):
    with patch("src.app.api.router.get_db", new_callable=AsyncMock) as mock_get_db:
        mock_session = AsyncMock()
        mock_get_db.return_value.__aenter__.return_value = mock_session
        response = client.put("/users/0", json=valid_user_update_data)
        assert response.status_code == 404

def test_delete_user_invalid_id(client):
    with patch("src.app.api.router.get_db", new_callable=AsyncMock) as mock_get_db:
        mock_session = AsyncMock()
        mock_get_db.return_value.__aenter__.return_value = mock_session
        response = client.delete("/users/0")
        assert response.status_code == 404