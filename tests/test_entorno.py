import pytest
from fastapi.testclient import TestClient
from src.app.routers.users import router
from src.app.schemas import UserCreate, UserUpdate, User
from unittest.mock import patch, MagicMock
from sqlalchemy.orm import Session
from datetime import date

# Fixtures
@pytest.fixture
def client():
    from src.main import app
    app.include_router(router)
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
def mock_db_session():
    session = MagicMock(spec=Session)
    return session

# Tests de funcionalidad básica
def test_create_user_valid_data(client, valid_user_data):
    response = client.post("/users/", json=valid_user_data)
    assert response.status_code == 200
    user = response.json()
    assert user["username"] == valid_user_data["username"]
    assert user["email"] == valid_user_data["email"]

def test_read_users(client, mock_db_session):
    with patch('src.app.routers.users.get_db', return_value=mock_db_session):
        mock_db_session.query.return_value.all.return_value = [
            User(
                id=1,
                username="testuser",
                email="test@example.com",
                first_name="John",
                last_name="Doe",
                date_of_birth=date(1990, 1, 1)
            )
        ]
        response = client.get("/users/")
        assert response.status_code == 200
        users = response.json()
        assert len(users) == 1

def test_read_user_by_id(client, mock_db_session):
    with patch('src.app.routers.users.get_db', return_value=mock_db_session):
        mock_db_session.query.return_value.filter.return_value.first.return_value = User(
            id=1,
            username="testuser",
            email="test@example.com",
            first_name="John",
            last_name="Doe",
            date_of_birth=date(1990, 1, 1)
        )
        response = client.get("/users/1")
        assert response.status_code == 200
        user = response.json()
        assert user["id"] == 1

def test_update_user_valid_data(client, valid_user_update_data):
    with patch('src.app.routers.users.get_db', return_value=mock_db_session):
        mock_db_session.query.return_value.filter.return_value.first.return_value = User(
            id=1,
            username="testuser",
            email="test@example.com",
            first_name="John",
            last_name="Doe",
            date_of_birth=date(1990, 1, 1)
        )
        response = client.put("/users/1", json=valid_user_update_data)
        assert response.status_code == 200
        user = response.json()
        assert user["first_name"] == valid_user_update_data["first_name"]
        assert user["last_name"] == valid_user_update_data["last_name"]

def test_delete_user(client, mock_db_session):
    with patch('src.app.routers.users.get_db', return_value=mock_db_session):
        mock_db_session.query.return_value.filter.return_value.first.return_value = User(
            id=1,
            username="testuser",
            email="test@example.com",
            first_name="John",
            last_name="Doe",
            date_of_birth=date(1990, 1, 1)
        )
        response = client.delete("/users/1")
        assert response.status_code == 200
        user = response.json()
        assert user["id"] == 1

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

def test_create_user_no_first_name_or_last_name(client, valid_user_data):
    user_data = {
        "username": valid_user_data["username"],
        "email": valid_user_data["email"],
        "password": valid_user_data["password"]
    }
    response = client.post("/users/", json=user_data)
    assert response.status_code == 200

def test_create_user_no_date_of_birth(client, valid_user_data):
    user_data = {
        "username": valid_user_data["username"],
        "email": valid_user_data["email"],
        "password": valid_user_data["password"]
    }
    response = client.post("/users/", json=user_data)
    assert response.status_code == 200

# Tests de manejo de errores
def test_create_user_invalid_email(client):
    user_data = {
        "username": "testuser",
        "email": "invalid-email",
        "password": "securepassword123"
    }
    response = client.post("/users/", json=user_data)
    assert response.status_code == 422

def test_create_user_password_too_short(client):
    user_data = {
        "username": "testuser",
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

def test_read_user_by_invalid_id(client, mock_db_session):
    with patch('src.app.routers.users.get_db', return_value=mock_db_session):
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        response = client.get("/users/0")
        assert response.status_code == 404

def test_update_user_invalid_id(client, valid_user_update_data, mock_db_session):
    with patch('src.app.routers.users.get_db', return_value=mock_db_session):
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        response = client.put("/users/0", json=valid_user_update_data)
        assert response.status_code == 404

def test_delete_user_invalid_id(client, mock_db_session):
    with patch('src.app.routers.users.get_db', return_value=mock_db_session):
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        response = client.delete("/users/0")
        assert response.status_code == 404