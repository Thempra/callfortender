import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.main import app
from app.models.user_model import UserCreate, UserInDB
from app.repositories.user_repository import UserRepository

# Fixtures
@pytest.fixture(scope="module")
async def test_db():
    from app.database import engine, Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture(scope="module")
def client(test_db):
    return TestClient(app)

@pytest.fixture(scope="function")
async def user_in_db(test_db):
    from app.database import get_async_session
    session: AsyncSession = next(get_async_session())
    user = UserCreate(username="testuser", email="test@example.com", password="securepassword123")
    repo = UserRepository(session)
    await repo.create_user(user)
    await session.commit()
    return user

# Tests de funcionalidad básica
def test_create_user(client):
    user_data = {
        "username": "newuser",
        "email": "new@example.com",
        "password": "securepassword123"
    }
    response = client.post("/users/", json=user_data)
    assert response.status_code == 200
    created_user = response.json()
    assert created_user["username"] == user_data["username"]
    assert created_user["email"] == user_data["email"]

def test_read_users(client, user_in_db):
    response = client.get("/users/")
    assert response.status_code == 200
    users = response.json()
    assert len(users) > 0

def test_read_user_by_id(client, user_in_db):
    response = client.get("/users/1")
    assert response.status_code == 200
    user = response.json()
    assert user["username"] == user_in_db.username

def test_update_user(client, user_in_db):
    update_data = {
        "first_name": "John",
        "last_name": "Doe"
    }
    response = client.put("/users/1", json=update_data)
    assert response.status_code == 200
    updated_user = response.json()
    assert updated_user["first_name"] == update_data["first_name"]
    assert updated_user["last_name"] == update_data["last_name"]

def test_delete_user(client, user_in_db):
    response = client.delete("/users/1")
    assert response.status_code == 200
    deleted_user = response.json()
    assert deleted_user["username"] == user_in_db.username

# Tests de edge cases
def test_create_user_min_length_username(client):
    user_data = {
        "username": "us",
        "email": "test@example.com",
        "password": "securepassword123"
    }
    response = client.post("/users/", json=user_data)
    assert response.status_code == 422

def test_create_user_max_length_username(client):
    user_data = {
        "username": "a" * 50,
        "email": "test@example.com",
        "password": "securepassword123"
    }
    response = client.post("/users/", json=user_data)
    assert response.status_code == 200

def test_create_user_no_first_name_or_last_name(client):
    user_data = {
        "username": "newuser",
        "email": "new@example.com",
        "password": "securepassword123"
    }
    response = client.post("/users/", json=user_data)
    assert response.status_code == 200

def test_create_user_no_date_of_birth(client):
    user_data = {
        "username": "newuser",
        "email": "new@example.com",
        "password": "securepassword123"
    }
    response = client.post("/users/", json=user_data)
    assert response.status_code == 200

# Tests de manejo de errores
def test_create_user_invalid_email(client):
    user_data = {
        "username": "newuser",
        "email": "invalid-email",
        "password": "securepassword123"
    }
    response = client.post("/users/", json=user_data)
    assert response.status_code == 422

def test_create_user_password_too_short(client):
    user_data = {
        "username": "newuser",
        "email": "test@example.com",
        "password": "short"
    }
    response = client.post("/users/", json=user_data)
    assert response.status_code == 422

def test_create_user_invalid_username_length(client):
    user_data = {
        "username": "a" * 51,
        "email": "test@example.com",
        "password": "securepassword123"
    }
    response = client.post("/users/", json=user_data)
    assert response.status_code == 422

def test_read_user_by_invalid_id(client):
    response = client.get("/users/0")
    assert response.status_code == 404

def test_update_user_invalid_id(client, user_in_db):
    update_data = {
        "first_name": "John",
        "last_name": "Doe"
    }
    response = client.put("/users/0", json=update_data)
    assert response.status_code == 404

def test_delete_user_invalid_id(client):
    response = client.delete("/users/0")
    assert response.status_code == 404