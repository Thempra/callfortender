import pytest
from fastapi.testclient import TestClient
from src.convocatoria import (
    ConvocatoriaBase,
    ConvocatoriaCreate,
    ConvocatoriaUpdate,
    ConvocatoriaInDBBase,
    Convocatoria,
    ConvocatoriaModel,
    ConvocatoriaRepository,
    get_db,
    app
)
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock
from datetime import date

# Fixtures
@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def async_session():
    return AsyncMock(spec=AsyncSession)

@pytest.fixture
def convocation_repository(async_session):
    return ConvocatoriaRepository(session=async_session)

@pytest.fixture
def valid_convocation_data():
    return {
        "titulo": "Convocatoria de Prueba",
        "descripcion": "Esta es una convocatoria de prueba.",
        "fecha_inicio": date(2023, 10, 1),
        "fecha_fin": date(2023, 10, 31)
    }

@pytest.fixture
def valid_convocation_update_data():
    return {
        "titulo": "Convocatoria Actualizada",
        "descripcion": "Esta es una convocatoria actualizada.",
        "fecha_inicio": date(2023, 10, 1),
        "fecha_fin": date(2023, 11, 30)
    }

# Tests de funcionalidad básica
def test_create_convocation_valid_data(convocation_repository, valid_convocation_data):
    db_convocation = ConvocatoriaInDB(id=1, **valid_convocation_data)
    convocation_repository.session.add.return_value = None
    convocation_repository.session.commit.return_value = None
    convocation_repository.session.refresh.return_value = None
    result = convocation_repository.create(ConvocatoriaCreate(**valid_convocation_data))
    assert result.id == 1
    assert result.titulo == valid_convocation_data["titulo"]
    assert result.descripcion == valid_convocation_data["descripcion"]

def test_get_all_convolations(convocation_repository, valid_convocation_data):
    db_convocations = [ConvocatoriaInDB(id=1, **valid_convocation_data)]
    convocation_repository.session.execute.return_value.scalars.return_value.all.return_value = db_convocations
    result = convocation_repository.get_all()
    assert len(result) == 1
    assert result[0].id == 1

def test_get_convocation_by_id(convocation_repository, valid_convocation_data):
    db_convocation = ConvocatoriaInDB(id=1, **valid_convocation_data)
    convocation_repository.session.execute.return_value.scalars.return_value.first.return_value = db_convocation
    result = convocation_repository.get_by_id(1)
    assert result.id == 1

# Tests de edge cases
def test_create_convocation_min_length_title(convocation_repository):
    data = {
        "titulo": "C" * 5,
        "descripcion": "Esta es una convocatoria de prueba.",
        "fecha_inicio": date(2023, 10, 1),
        "fecha_fin": date(2023, 10, 31)
    }
    db_convocation = ConvocatoriaInDB(id=1, **data)
    convocation_repository.session.add.return_value = None
    convocation_repository.session.commit.return_value = None
    convocation_repository.session.refresh.return_value = None
    result = convocation_repository.create(ConvocatoriaCreate(**data))
    assert result.id == 1

def test_create_convocation_max_length_title(convocation_repository):
    data = {
        "titulo": "C" * 100,
        "descripcion": "Esta es una convocatoria de prueba.",
        "fecha_inicio": date(2023, 10, 1),
        "fecha_fin": date(2023, 10, 31)
    }
    db_convocation = ConvocatoriaInDB(id=1, **data)
    convocation_repository.session.add.return_value = None
    convocation_repository.session.commit.return_value = None
    convocation_repository.session.refresh.return_value = None
    result = convocation_repository.create(ConvocatoriaCreate(**data))
    assert result.id == 1

def test_create_convocation_with_none_description(convocation_repository, valid_convocation_data):
    data = {
        **valid_convocation_data,
        "descripcion": None
    }
    with pytest.raises(ValueError):
        ConvocatoriaCreate(**data)

# Tests de manejo de errores
def test_create_convocation_with_empty_title(convocation_repository, valid_convocation_data):
    data = {
        **valid_convocation_data,
        "titulo": ""
    }
    with pytest.raises(ValueError):
        ConvocatoriaCreate(**data)

def test_get_convocation_by_invalid_id(convocation_repository):
    convocation_repository.session.execute.return_value.scalars.return_value.first.return_value = None
    result = convocation_repository.get_by_id(0)
    assert result is None

def test_create_convocation_no_description(convocation_repository, valid_convocation_data):
    data = {
        "titulo": "Convocatoria de Prueba",
        "fecha_inicio": date(2023, 10, 1),
        "fecha_fin": date(2023, 10, 31)
    }
    with pytest.raises(ValueError):
        ConvocatoriaCreate(**data)

def test_create_convocation_invalid_date_range(convocation_repository):
    data = {
        "titulo": "Convocatoria de Prueba",
        "descripcion": "Esta es una convocatoria de prueba.",
        "fecha_inicio": date(2023, 10, 31),
        "fecha_fin": date(2023, 10, 1)
    }
    with pytest.raises(ValueError):
        ConvocatoriaCreate(**data)

def test_create_convocation_invalid_length_title(convocation_repository):
    data = {
        "titulo": "C" * 4,
        "descripcion": "Esta es una convocatoria de prueba.",
        "fecha_inicio": date(2023, 10, 1),
        "fecha_fin": date(2023, 10, 31)
    }
    with pytest.raises(ValueError):
        ConvocatoriaCreate(**data)

def test_create_convocation_invalid_length_title_max(convocation_repository):
    data = {
        "titulo": "C" * 101,
        "descripcion": "Esta es una convocatoria de prueba.",
        "fecha_inicio": date(2023, 10, 1),
        "fecha_fin": date(2023, 10, 31)
    }
    with pytest.raises(ValueError):
        ConvocatoriaCreate(**data)