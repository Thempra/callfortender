import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.schemas.call_schema import CallCreate, CallUpdate
from app.schemas.user_schema import UserCreate, UserUpdate
from unittest.mock import AsyncMock

# Fixtures
@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def valid_call_data():
    return {
        "caller_id": 1,
        "callee_id": 2,
        "duration": 60
    }

@pytest.fixture
def valid_user_data():
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "securepassword123",
        "first_name": "John",
        "last_name": "Doe",
        "date_of_birth": "1990-01-01"
    }

@pytest.fixture
def call_service_mock():
    mock = AsyncMock()
    mock.create_call.return_value = {
        "id": 1,
        **valid_call_data
    }
    mock.get_calls.return_value = [
        {
            "id": 1,
            **valid_call_data
        }
    ]
    mock.get_call_by_id.return_value = {
        "id": 1,
        **valid_call_data
    }
    mock.update_call.return_value = {
        "id": 1,
        **valid_call_data
    }
    mock.delete_call.return_value = {
        "id": 1,
        **valid_call_data
    }
    return mock

@pytest.fixture
def user_service_mock():
    mock = AsyncMock()
    mock.create_user.return_value = {
        "id": 1,
        **valid_user_data
    }
    mock.get_users.return_value = [
        {
            "id": 1,
            **valid_user_data
        }
    ]
    mock.get_user_by_id.return_value = {
        "id": 1,
        **valid_user_data
    }
    mock.update_user.return_value = {
        "id": 1,
        **valid_user_data
    }
    mock.delete_user.return_value = {
        "id": 1,
        **valid_user_data
    }
    return mock

@pytest.fixture
def app_with_mocked_services(client, call_service_mock, user_service_mock):
    from app.dependencies import get_call_service, get_user_service
    get_call_service.__wrapped__ = lambda: call_service_mock
    get_user_service.__wrapped__ = lambda: user_service_mock
    return client

# Tests de funcionalidad básica
def test_create_call_valid_data(app_with_mocked_services, valid_call_data):
    response = app_with_mocked_services.post("/calls/", json=valid_call_data)
    assert response.status_code == 200
    call = response.json()
    assert call["caller_id"] == valid_call_data["caller_id"]
    assert call["callee_id"] == valid_call_data["callee_id"]
    assert call["duration"] == valid_call_data["duration"]

def test_read_calls(app_with_mocked_services):
    response = app_with_mocked_services.get("/calls/")
    assert response.status_code == 200
    calls = response.json()
    assert len(calls) == 1

def test_read_call_by_id(app_with_mocked_services):
    response = app_with_mocked_services.get("/calls/1")
    assert response.status_code == 200
    call = response.json()
    assert call["id"] == 1

def test_update_call_valid_data(app_with_mocked_services, valid_call_data):
    update_data = {"duration": 120}
    response = app_with_mocked_services.put("/calls/1", json=update_data)
    assert response.status_code == 200
    call = response.json()
    assert call["duration"] == update_data["duration"]

def test_delete_call(app_with_mocked_services):
    response = app_with_mocked_services.delete("/calls/1")
    assert response.status_code == 200
    call = response.json()
    assert call["id"] == 1

def test_create_user_valid_data(app_with_mocked_services, valid_user_data):
    response = app_with_mocked_services.post("/users/", json=valid_user_data)
    assert response.status_code == 200
    user = response.json()
    assert user["username"] == valid_user_data["username"]
    assert user["email"] == valid_user_data["email"]

def test_read_users(app_with_mocked_services):
    response = app_with_mocked_services.get("/users/")
    assert response.status_code == 200
    users = response.json()
    assert len(users) == 1

def test_read_user_by_id(app_with_mocked_services):
    response = app_with_mocked_services.get("/users/1")
    assert response.status_code == 200
    user = response.json()
    assert user["id"] == 1

def test_update_user_valid_data(app_with_mocked_services, valid_user_data):
    update_data = {"first_name": "Jane", "last_name": "Smith"}
    response = app_with_mocked_services.put("/users/1", json=update_data)
    assert response.status_code == 200
    user = response.json()
    assert user["first_name"] == update_data["first_name"]
    assert user["last_name"] == update_data["last_name"]

def test_delete_user(app_with_mocked_services):
    response = app_with_mocked_services.delete("/users/1")
    assert response.status_code == 200
    user = response.json()
    assert user["id"] == 1

# Tests de edge cases
def test_create_call_min_duration(app_with_mocked_services, valid_call_data):
    call_data = {**valid_call_data, "duration": 0}
    response = app_with_mocked_services.post("/calls/", json=call_data)
    assert response.status_code == 200

def test_create_user_min_length_username(app_with_mocked_services):
    user_data = {
        "username": "us",
        "email": "test@example.com",
        "password": "securepassword123",
        "first_name": "John",
        "last_name": "Doe",
        "date_of_birth": "1990-01-01"
    }
    response = app_with_mocked_services.post("/users/", json=user_data)
    assert response.status_code == 422

def test_create_user_max_length_username(app_with_mocked_services):
    user_data = {
        "username": "a" * 50,
        "email": "test@example.com",
        "password": "securepassword123",
        "first_name": "John",
        "last_name": "Doe",
        "date_of_birth": "1990-01-01"
    }
    response = app_with_mocked_services.post("/users/", json=user_data)
    assert response.status_code == 200

def test_create_user_no_first_name_or_last_name(app_with_mocked_services, valid_user_data):
    user_data = {
        "username": valid_user_data["username"],
        "email": valid_user_data["email"],
        "password": valid_user_data["password"]
    }
    response = app_with_mocked_services.post("/users/", json=user_data)
    assert response.status_code == 422

def test_create_user_no_date_of_birth(app_with_mocked_services, valid_user_data):
    user_data = {
        "username": valid_user_data["username"],
        "email": valid_user_data["email"],
        "password": valid_user_data["password"],
        "first_name": valid_user_data["first_name"],
        "last_name": valid_user_data["last_name"]
    }
    response = app_with_mocked_services.post("/users/", json=user_data)
    assert response.status_code == 422

# Tests de manejo de errores
def test_create_call_invalid_duration(app_with_mocked_services, valid_call_data):
    call_data = {**valid_call_data, "duration": -1}
    response = app_with_mocked_services.post("/calls/", json=call_data)
    assert response.status_code == 422

def test_create_user_invalid_email(app_with_mocked_services):
    user_data = {
        "username": "testuser",
        "email": "invalid-email",
        "password": "securepassword123",
        "first_name": "John",
        "last_name": "Doe",
        "date_of_birth": "1990-01-01"
    }
    response = app_with_mocked_services.post("/users/", json=user_data)
    assert response.status_code == 422

def test_create_user_password_too_short(app_with_mocked_services):
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "short",
        "first_name": "John",
        "last_name": "Doe",
        "date_of_birth": "1990-01-01"
    }
    response = app_with_mocked_services.post("/users/", json=user_data)
    assert response.status_code == 422

def test_create_user_invalid_username_length(app_with_mocked_services):
    user_data = {
        "username": "a" * 51,
        "email": "test@example.com",
        "password": "securepassword123",
        "first_name": "John",
        "last_name": "Doe",
        "date_of_birth": "1990-01-01"
    }
    response = app_with_mocked_services.post("/users/", json=user_data)
    assert response.status_code == 422

def test_read_call_by_invalid_id(app_with_mocked_services):
    response = app_with_mocked_services.get("/calls/0")
    assert response.status_code == 404

def test_update_call_invalid_id(app_with_mocked_services, valid_call_data):
    update_data = {"duration": 120}
    response = app_with_mocked_services.put("/calls/0", json=update_data)
    assert response.status_code == 404

def test_delete_call_invalid_id(app_with_mocked_services):
    response = app_with_mocked_services.delete("/calls/0")
    assert response.status_code == 404

def test_read_user_by_invalid_id(app_with_mocked_services):
    response = app_with_mocked_services.get("/users/0")
    assert response.status_code == 404

def test_update_user_invalid_id(app_with_mocked_services, valid_user_data):
    update_data = {"first_name": "Jane", "last_name": "Smith"}
    response = app_with_mocked_services.put("/users/0", json=update_data)
    assert response.status_code == 404

def test_delete_user_invalid_id(app_with_mocked_services):
    response = app_with_mocked_services.delete("/users/0")
    assert response.status_code == 404