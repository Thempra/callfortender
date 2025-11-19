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
        "publication_date": date(2023, 10, 1),
        "end_date": date(2023, 10, 31)
    }

@pytest.fixture
def valid_convocation_update_data():
    return {
        "title": "Convocatoria Actualizada",
        "description": "Esta es una convocatoria actualizada.",
        "publication_date": date(2023, 10, 1),
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
    convocation = ConvocationInDB(**valid_convocation_data, id=1)
    convocation_repository.create.return_value = convocation
    result = convocation_repository.create(ConvocationCreate(**valid_convocation_data))
    assert result.id == 1
    assert result.title == valid_convocation_data["title"]
    assert result.description == valid_convocation_data["description"]

def test_update_convocation_valid_data(convocation_repository, valid_convocation_update_data):
    updated_convocation = ConvocationInDB(id=1, **valid_convocation_update_data)
    convocation_repository.update.return_value = updated_convocation
    result = convocation_repository.update(1, ConvocationUpdate(**valid_convocation_update_data))
    assert result.id == 1
    assert result.title == valid_convocation_update_data["title"]
    assert result.description == valid_convocation_update_data["description"]

def test_get_all_convolations(convocation_repository):
    convocations = [ConvocationInDB(id=1, **valid_convocation_data)]
    convocation_repository.get_all.return_value = convocations
    result = convocation_repository.get_all()
    assert len(result) == 1
    assert result[0].id == 1

def test_get_convocation_by_id(convocation_repository, valid_convocation_data):
    convocation = ConvocationInDB(id=1, **valid_convocation_data)
    convocation_repository.get_by_id.return_value = convocation
    result = convocation_repository.get_by_id(1)
    assert result.id == 1

# Tests de edge cases
def test_create_convocation_min_length_title(convocation_repository):
    data = {
        "title": "C",
        "description": "Esta es una convocatoria de prueba.",
        "publication_date": date(2023, 10, 1),
        "end_date": date(2023, 10, 31)
    }
    with pytest.raises(ValueError):
        ConvocationCreate(**data)

def test_create_convocation_max_length_title(convocation_repository):
    data = {
        "title": "C" * 50,
        "description": "Esta es una convocatoria de prueba.",
        "publication_date": date(2023, 10, 1),
        "end_date": date(2023, 10, 31)
    }
    convocation = ConvocationInDB(**data, id=1)
    convocation_repository.create.return_value = convocation
    result = convocation_repository.create(ConvocationCreate(**data))
    assert result.id == 1

def test_create_convocation_no_description(convocation_repository):
    data = {
        "title": "Convocatoria de Prueba",
        "publication_date": date(2023, 10, 1),
        "end_date": date(2023, 10, 31)
    }
    convocation = ConvocationInDB(**data, id=1)
    convocation_repository.create.return_value = convocation
    result = convocation_repository.create(ConvocationCreate(**data))
    assert result.id == 1

# Tests de manejo de errores
def test_create_convocation_invalid_date_range(convocation_repository):
    data = {
        "title": "Convocatoria de Prueba",
        "description": "Esta es una convocatoria de prueba.",
        "publication_date": date(2023, 10, 31),
        "end_date": date(2023, 10, 1)
    }
    with pytest.raises(ValueError):
        ConvocationCreate(**data)

def test_get_convocation_by_invalid_id(convocation_repository):
    convocation_repository.get_by_id.return_value = None
    result = convocation_repository.get_by_id(0)
    assert result is None

def test_update_convocation_non_existent_id(convocation_repository, valid_convocation_update_data):
    convocation_repository.update.return_value = None
    result = convocation_repository.update(0, ConvocationUpdate(**valid_convocation_update_data))
    assert result is None