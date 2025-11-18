import pytest
from pydantic import ValidationError
from datetime import date
from src.user_model import UserBase, UserCreate, UserUpdate, UserInDBBase, User, UserInDB

# Fixtures
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
def valid_user_in_db_data():
    return {
        "id": 1,
        "username": "testuser",
        "email": "test@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "date_of_birth": date(1990, 1, 1),
        "hashed_password": "hashedpassword"
    }

# Tests de funcionalidad básica
def test_create_user_valid_data(valid_user_data):
    user = UserCreate(**valid_user_data)
    assert user.username == valid_user_data["username"]
    assert user.email == valid_user_data["email"]
    assert user.password == valid_user_data["password"]

def test_user_in_db_valid_data(valid_user_in_db_data):
    user_in_db = UserInDB(**valid_user_in_db_data)
    assert user_in_db.id == valid_user_in_db_data["id"]
    assert user_in_db.username == valid_user_in_db_data["username"]
    assert user_in_db.email == valid_user_in_db_data["email"]
    assert user_in_db.hashed_password == valid_user_in_db_data["hashed_password"]

# Tests de edge cases
def test_create_user_min_length_username():
    user = UserCreate(username="us", email="test@example.com", password="securepassword123")
    assert user.username == "us"

def test_create_user_max_length_username():
    user = UserCreate(username="a" * 50, email="test@example.com", password="securepassword123")
    assert user.username == "a" * 50

def test_create_user_no_first_name_or_last_name():
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "securepassword123"
    }
    user = UserCreate(**user_data)
    assert user.first_name is None
    assert user.last_name is None

def test_create_user_no_date_of_birth():
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "securepassword123"
    }
    user = UserCreate(**user_data)
    assert user.date_of_birth is None

# Tests de manejo de errores
def test_create_user_invalid_email():
    with pytest.raises(ValidationError):
        UserCreate(username="testuser", email="invalid-email", password="securepassword123")

def test_create_user_password_too_short():
    with pytest.raises(ValidationError):
        UserCreate(username="testuser", email="test@example.com", password="short")

def test_create_user_invalid_username_length():
    with pytest.raises(ValidationError):
        UserCreate(username="a" * 51, email="test@example.com", password="securepassword123")
    
    with pytest.raises(ValidationError):
        UserCreate(username="", email="test@example.com", password="securepassword123")

def test_user_in_db_missing_id():
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "date_of_birth": date(1990, 1, 1),
        "hashed_password": "hashedpassword"
    }
    with pytest.raises(ValidationError):
        UserInDB(**user_data)

def test_user_in_db_missing_hashed_password():
    user_data = {
        "id": 1,
        "username": "testuser",
        "email": "test@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "date_of_birth": date(1990, 1, 1)
    }
    with pytest.raises(ValidationError):
        UserInDB(**user_data)