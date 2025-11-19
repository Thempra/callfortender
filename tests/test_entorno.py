import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock
from datetime import datetime
from src.app.call.call_model import CallBase, CallCreate, CallUpdate, CallInDBBase, Call, CallInDB
from src.app.call.call_repository import CallRepository

# Fixtures
@pytest.fixture
def client():
    from fastapi import FastAPI
    app = FastAPI()
    return TestClient(app)

@pytest.fixture
async def async_session_mock():
    session = AsyncMock(spec=AsyncSession)
    return session

@pytest.fixture
def call_create_data():
    return {
        "caller_id": 1,
        "callee_id": 2,
        "call_start_time": datetime.now(),
        "call_end_time": datetime.now()
    }

@pytest.fixture
def call_update_data():
    return {
        "call_end_time": datetime.now()
    }

# Tests de funcionalidad básica
async def test_create_call_valid_data(async_session_mock, call_create_data):
    repository = CallRepository(session=async_session_mock)
    async_session_mock.add.return_value = None
    async_session_mock.commit.return_value = None
    async_session_mock.refresh.return_value = None

    call_create = CallCreate(**call_create_data)
    result = await repository.create(call_create)

    assert isinstance(result, CallInDB)
    assert result.caller_id == call_create_data["caller_id"]
    assert result.callee_id == call_create_data["callee_id"]

async def test_get_all_calls(async_session_mock):
    repository = CallRepository(session=async_session_mock)
    async_session_mock.execute.return_value.scalars.return_value.all.return_value = [
        CallInDB(id=1, caller_id=1, callee_id=2, call_start_time=datetime.now(), call_end_time=datetime.now()),
        CallInDB(id=2, caller_id=3, callee_id=4, call_start_time=datetime.now(), call_end_time=datetime.now())
    ]

    result = await repository.get_all()

    assert len(result) == 2
    assert all(isinstance(call, CallInDB) for call in result)

async def test_get_call_by_id(async_session_mock):
    repository = CallRepository(session=async_session_mock)
    async_session_mock.execute.return_value.scalars.return_value.first.return_value = CallInDB(
        id=1, caller_id=1, callee_id=2, call_start_time=datetime.now(), call_end_time=datetime.now()
    )

    result = await repository.get_by_id(1)

    assert isinstance(result, CallInDB)
    assert result.id == 1

async def test_update_call_valid_data(async_session_mock, call_update_data):
    repository = CallRepository(session=async_session_mock)
    async_session_mock.commit.return_value = None
    async_session_mock.refresh.return_value = None

    call_to_update = CallInDB(id=1, caller_id=1, callee_id=2, call_start_time=datetime.now(), call_end_time=None)
    result = await repository.update(call_to_update, CallUpdate(**call_update_data))

    assert isinstance(result, CallInDB)
    assert result.call_end_time == call_update_data["call_end_time"]

# Tests de edge cases
async def test_create_call_with_none_values(async_session_mock):
    repository = CallRepository(session=async_session_mock)
    async_session_mock.add.return_value = None
    async_session_mock.commit.return_value = None
    async_session_mock.refresh.return_value = None

    call_create_data = {
        "caller_id": 1,
        "callee_id": 2,
        "call_start_time": datetime.now(),
        "call_end_time": None
    }
    call_create = CallCreate(**call_create_data)
    result = await repository.create(call_create)

    assert isinstance(result, CallInDB)
    assert result.caller_id == call_create_data["caller_id"]
    assert result.callee_id == call_create_data["callee_id"]
    assert result.call_end_time is None

async def test_get_call_by_nonexistent_id(async_session_mock):
    repository = CallRepository(session=async_session_mock)
    async_session_mock.execute.return_value.scalars.return_value.first.return_value = None

    result = await repository.get_by_id(999)

    assert result is None

# Tests de manejo de errores
async def test_create_call_invalid_data(async_session_mock):
    repository = CallRepository(session=async_session_mock)
    async_session_mock.add.side_effect = Exception("Database error")

    call_create_data = {
        "caller_id": 1,
        "callee_id": 2,
        "call_start_time": datetime.now(),
        "call_end_time": None
    }
    call_create = CallCreate(**call_create_data)

    try:
        await repository.create(call_create)
    except Exception as e:
        assert str(e) == "Database error"

async def test_update_call_invalid_id(async_session_mock, call_update_data):
    repository = CallRepository(session=async_session_mock)
    async_session_mock.commit.side_effect = Exception("Database error")

    call_to_update = CallInDB(id=999, caller_id=1, callee_id=2, call_start_time=datetime.now(), call_end_time=None)

    try:
        await repository.update(call_to_update, CallUpdate(**call_update_data))
    except Exception as e:
        assert str(e) == "Database error"