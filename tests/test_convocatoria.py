import pytest
from fastapi.testclient import TestClient
from src.app.models.convocation_model import ConvocationBase, ConvocationCreate, ConvocationUpdate, ConvocationInDBBase, Convocation, ConvocationInDB
from src.app.repositories.convocation_repository import ConvocationRepository
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock
from datetime import date

# Fixtures
@pytest.fixture
def client():
    from fastapi import FastAPI
    app = FastAPI()
    return TestClient(app)

@pytest.fixture
def valid_convocation_data():
    return {
        "title": "Convocatoria de Prueba",
        "description": "Esta es una convocatoria de prueba.",
        "start_date": date(2023, 10, 1),
        "end_date": date(2023, 10, 31)
    }

@pytest.fixture
def valid_convocation_update_data():
    return {
        "title": "Convocatoria Actualizada",
        "description": "Esta es una convocatoria actualizada.",
        "start_date": date(2023, 10, 1),
        "end_date": date(2023, 11, 30)
    }

@pytest.fixture
def async_session():
    return AsyncMock(spec=AsyncSession)

@pytest.fixture
def convocation_repository(async_session):
    return ConvocationRepository(session=async_session)

# Tests de funcionalidad básica
def test_create_convocation_valid_data(convocation_repository, valid_convocation_data):
    db_convocation = ConvocationInDB(id=1, **valid_convocation_data)
    convocation_repository.session.add.return_value = None
    convocation_repository.session.commit.return_value = None
    convocation_repository.session.refresh.return_value = None
    result = convocation_repository.create(ConvocationCreate(**valid_convocation_data))
    assert result.id == 1
    assert result.title == valid_convocation_data["title"]
    assert result.description == valid_convocation_data["description"]

def test_get_all_convolations(convocation_repository, valid_convocation_data):
    db_convocations = [ConvocationInDB(id=1, **valid_convocation_data)]
    convocation_repository.session.execute.return_value.scalars.return_value.all.return_value = db_convocations
    result = convocation_repository.get_all()
    assert len(result) == 1
    assert result[0].id == 1

def test_get_convocation_by_id(convocation_repository, valid_convocation_data):
    db_convocation = ConvocationInDB(id=1, **valid_convocation_data)
    convocation_repository.session.execute.return_value.scalars.return_value.first.return_value = db_convocation
    result = convocation_repository.get_by_id(1)
    assert result.id == 1

# Tests de edge cases
def test_create_convocation_min_length_title(convocation_repository):
    data = {
        "title": "C",
        "description": "Esta es una convocatoria de prueba.",
        "start_date": date(2023, 10, 1),
        "end_date": date(2023, 10, 31)
    }
    with pytest.raises(ValueError):
        ConvocationCreate(**data)

def test_create_convocation_max_length_title(convocation_repository):
    data = {
        "title": "C" * 50,
        "description": "Esta es una convocatoria de prueba.",
        "start_date": date(2023, 10, 1),
        "end_date": date(2023, 10, 31)
    }
    db_convocation = ConvocationInDB(id=1, **data)
    convocation_repository.session.add.return_value = None
    convocation_repository.session.commit.return_value = None
    convocation_repository.session.refresh.return_value = None
    result = convocation_repository.create(ConvocationCreate(**data))
    assert result.id == 1

def test_create_convocation_no_description(convocation_repository):
    data = {
        "title": "Convocatoria de Prueba",
        "start_date": date(2023, 10, 1),
        "end_date": date(2023, 10, 31)
    }
    with pytest.raises(ValueError):
        ConvocationCreate(**data)

def test_create_convocation_invalid_date_range(convocation_repository):
    data = {
        "title": "Convocatoria de Prueba",
        "description": "Esta es una convocatoria de prueba.",
        "start_date": date(2023, 10, 31),
        "end_date": date(2023, 10, 1)
    }
    with pytest.raises(ValueError):
        ConvocationCreate(**data)

def test_create_convocation_with_location(convocation_repository, valid_convocation_data):
    data = {
        **valid_convocation_data,
        "location": "Ciudad de Prueba"
    }
    db_convocation = ConvocationInDB(id=1, **data)
    convocation_repository.session.add.return_value = None
    convocation_repository.session.commit.return_value = None
    convocation_repository.session.refresh.return_value = None
    result = convocation_repository.create(ConvocationCreate(**data))
    assert result.id == 1
    assert result.location == "Ciudad de Prueba"

# Tests de manejo de errores
def test_get_convocation_by_invalid_id(convocation_repository):
    convocation_repository.session.execute.return_value.scalars.return_value.first.return_value = None
    result = convocation_repository.get_by_id(0)
    assert result is None

def test_create_convocation_with_empty_title(convocation_repository, valid_convocation_data):
    data = {
        **valid_convocation_data,
        "title": ""
    }
    with pytest.raises(ValueError):
        ConvocationCreate(**data)

def test_create_convocation_with_none_description(convocation_repository, valid_convocation_data):
    data = {
        **valid_convocation_data,
        "description": None
    }
    with pytest.raises(ValueError):
        ConvocationCreate(**data)