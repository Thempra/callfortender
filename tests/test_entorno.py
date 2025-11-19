import pytest
from fastapi.testclient import TestClient
from app.routers import users
from app.models.user_model import UserCreate, UserUpdate, User
from unittest.mock import AsyncMock
from datetime import date

# Fixtures
@pytest.fixture
def client():
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(users.router, prefix="/users", tags=["users"])
    return TestClient(app)

@pytest.fixture
def valid_user_data():
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "securepassword123",
        "first_name": "John",
        "last_name": "Doe",
        "date_of_birth": date(1990, 1, 1)
    }

@pytest.fixture
def valid_user_update_data():
    return {
        "first_name": "Jane",
        "last_name": "Smith"
    }

@pytest.fixture
def call_processing_service_mock():
    mock = AsyncMock()
    mock.create_user.return_value = User(
        id=1,
        username="testuser",
        email="test@example.com",
        first_name="John",
        last_name="Doe",
        date_of_birth=date(1990, 1, 1)
    )
    mock.get_user_by_id.return_value = User(
        id=1,
        username="testuser",
        email="test@example.com",
        first_name="John",
        last_name="Doe",
        date_of_birth=date(1990, 1, 1)
    )
    mock.update_user.return_value = User(
        id=1,
        username="testuser",
        email="test@example.com",
        first_name="Jane",
        last_name="Smith",
        date_of_birth=date(1990, 1, 1)
    )
    mock.delete_user.return_value = User(
        id=1,
        username="testuser",
        email="test@example.com",
        first_name="John",
        last_name="Doe",
        date_of_birth=date(1990, 1, 1)
    )
    return mock

@pytest.fixture
def app_with_mocked_service(client, call_processing_service_mock):
    from app.dependencies import get_call_processing_service
    get_call_processing_service.__wrapped__ = lambda: call_processing_service_mock
    return client

# Tests de funcionalidad básica
def test_create_user_valid_data(app_with_mocked_service, valid_user_data):
    response = app_with_mocked_service.post("/users/", json=valid_user_data)
    assert response.status_code == 200
    user = response.json()
    assert user["username"] == valid_user_data["username"]
    assert user["email"] == valid_user_data["email"]

def test_read_user_by_id(app_with_mocked_service):
    response = app_with_mocked_service.get("/users/1")
    assert response.status_code == 200
    user = response.json()
    assert user["id"] == 1

def test_update_user_valid_data(app_with_mocked_service, valid_user_update_data):
    response = app_with_mocked_service.put("/users/1", json=valid_user_update_data)
    assert response.status_code == 200
    user = response.json()
    assert user["first_name"] == valid_user_update_data["first_name"]
    assert user["last_name"] == valid_user_update_data["last_name"]

def test_delete_user(app_with_mocked_service):
    response = app_with_mocked_service.delete("/users/1")
    assert response.status_code == 200
    user = response.json()
    assert user["id"] == 1

# Tests de edge cases
def test_create_user_min_length_username(app_with_mocked_service):
    user_data = {
        "username": "us",
        "email": "test@example.com",
        "password": "securepassword123"
    }
    response = app_with_mocked_service.post("/users/", json=user_data)
    assert response.status_code == 422

def test_create_user_max_length_username(app_with_mocked_service):
    user_data = {
        "username": "a" * 50,
        "email": "test@example.com",
        "password": "securepassword123"
    }
    response = app_with_mocked_service.post("/users/", json=user_data)
    assert response.status_code == 200

def test_create_user_no_first_name_or_last_name(app_with_mocked_service, valid_user_data):
    user_data = {
        "username": valid_user_data["username"],
        "email": valid_user_data["email"],
        "password": valid_user_data["password"]
    }
    response = app_with_mocked_service.post("/users/", json=user_data)
    assert response.status_code == 200

def test_create_user_no_date_of_birth(app_with_mocked_service, valid_user_data):
    user_data = {
        "username": valid_user_data["username"],
        "email": valid_user_data["email"],
        "password": valid_user_data["password"]
    }
    response = app_with_mocked_service.post("/users/", json=user_data)
    assert response.status_code == 200

# Tests de manejo de errores
def test_create_user_invalid_email(app_with_mocked_service):
    user_data = {
        "username": "testuser",
        "email": "invalid-email",
        "password": "securepassword123"
    }
    response = app_with_mocked_service.post("/users/", json=user_data)
    assert response.status_code == 422

def test_create_user_password_too_short(app_with_mocked_service):
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "short"
    }
    response = app_with_mocked_service.post("/users/", json=user_data)
    assert response.status_code == 422

def test_create_user_invalid_username_length(app_with_mocked_service):
    user_data = {
        "username": "a" * 51,
        "email": "test@example.com",
        "password": "securepassword123"
    }
    response = app_with_mocked_service.post("/users/", json=user_data)
    assert response.status_code == 422

def test_read_user_by_invalid_id(app_with_mocked_service):
    response = app_with_mocked_service.get("/users/0")
    assert response.status_code == 404

def test_update_user_invalid_id(app_with_mocked_service, valid_user_update_data):
    response = app_with_mocked_service.put("/users/0", json=valid_user_update_data)
    assert response.status_code == 404

def test_delete_user_invalid_id(app_with_mocked_service):
    response = app_with_mocked_service.delete("/users/0")
    assert response.status_code == 404