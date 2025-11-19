import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.schemas.call_schema import CallCreate
from app.schemas.user_schema import UserCreate
from unittest.mock import AsyncMock

# Fixtures
@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def valid_call_data():
    return {
        "caller_id": 1,
        "receiver_id": 2,
        "call_time": "2023-10-01T12:00:00"
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
    mock.get_call_by_id.return_value = {
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
    mock.get_user_by_id.return_value = {
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
    assert call["receiver_id"] == valid_call_data["receiver_id"]

def test_create_user_valid_data(app_with_mocked_services, valid_user_data):
    response = app_with_mocked_services.post("/users/", json=valid_user_data)
    assert response.status_code == 200
    user = response.json()
    assert user["username"] == valid_user_data["username"]
    assert user["email"] == valid_user_data["email"]

def test_read_call_by_id(app_with_mocked_services):
    response = app_with_mocked_services.get("/calls/1")
    assert response.status_code == 200
    call = response.json()
    assert call["id"] == 1

def test_read_user_by_id(app_with_mocked_services):
    response = app_with_mocked_services.get("/users/1")
    assert response.status_code == 200
    user = response.json()
    assert user["id"] == 1

# Tests de edge cases
def test_create_call_min_values(app_with_mocked_services):
    call_data = {
        "caller_id": 1,
        "receiver_id": 2,
        "call_time": "2023-10-01T12:00:00"
    }
    response = app_with_mocked_services.post("/calls/", json=call_data)
    assert response.status_code == 200

def test_create_user_min_values(app_with_mocked_services):
    user_data = {
        "username": "user",
        "email": "u@e.com",
        "password": "pass"
    }
    response = app_with_mocked_services.post("/users/", json=user_data)
    assert response.status_code == 200

def test_create_call_no_optional_fields(app_with_mocked_services):
    call_data = {
        "caller_id": 1,
        "receiver_id": 2,
        "call_time": "2023-10-01T12:00:00"
    }
    response = app_with_mocked_services.post("/calls/", json=call_data)
    assert response.status_code == 200

def test_create_user_no_optional_fields(app_with_mocked_services):
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "securepassword123"
    }
    response = app_with_mocked_services.post("/users/", json=user_data)
    assert response.status_code == 200

# Tests de manejo de errores
def test_create_call_invalid_caller_id(app_with_mocked_services, valid_call_data):
    call_data = {
        **valid_call_data,
        "caller_id": None
    }
    response = app_with_mocked_services.post("/calls/", json=call_data)
    assert response.status_code == 422

def test_create_user_invalid_email(app_with_mocked_services, valid_user_data):
    user_data = {
        **valid_user_data,
        "email": "invalid-email"
    }
    response = app_with_mocked_services.post("/users/", json=user_data)
    assert response.status_code == 422

def test_create_call_password_too_short(app_with_mocked_services, valid_user_data):
    user_data = {
        **valid_user_data,
        "password": "sh"
    }
    response = app_with_mocked_services.post("/users/", json=user_data)
    assert response.status_code == 422

def test_read_call_by_invalid_id(app_with_mocked_services):
    response = app_with_mocked_services.get("/calls/0")
    assert response.status_code == 404

def test_read_user_by_invalid_id(app_with_mocked_services):
    response = app_with_mocked_services.get("/users/0")
    assert response.status_code == 404