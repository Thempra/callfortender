# tests/conftest.py

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from app.database import Base, get_db
from app.main import app

DATABASE_URL = "sqlite+aiosqlite:///./test.db"

engine = create_async_engine(DATABASE_URL, echo=True)
TestingSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

@pytest.fixture(scope="module")
async def test_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield TestingSessionLocal()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture(scope="module")
def client(test_db):
    app.dependency_overrides[get_db] = lambda: test_db
    return TestClient(app)


# tests/test_users.py

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.testclient import TestClient
from app.models.user_model import UserCreate, UserInDB
from app.repositories.user_repository import UserRepository

@pytest.mark.asyncio
async def test_create_user(client: TestClient, test_db: AsyncSession):
    user_data = UserCreate(
        username="testuser",
        email="test@example.com",
        password="password123"
    )
    response = client.post("/users/", json=user_data.dict())
    assert response.status_code == 201
    created_user = response.json()
    assert created_user["username"] == user_data.username
    assert created_user["email"] == user_data.email

@pytest.mark.asyncio
async def test_get_user(client: TestClient, test_db: AsyncSession):
    user_repo = UserRepository(test_db)
    db_user = UserInDB(
        username="testuser",
        email="test@example.com",
        hashed_password="hashedpassword"
    )
    test_db.add(db_user)
    await test_db.commit()
    response = client.get(f"/users/{db_user.id}")
    assert response.status_code == 200
    retrieved_user = response.json()
    assert retrieved_user["username"] == db_user.username
    assert retrieved_user["email"] == db_user.email

@pytest.mark.asyncio
async def test_update_user(client: TestClient, test_db: AsyncSession):
    user_repo = UserRepository(test_db)
    db_user = UserInDB(
        username="testuser",
        email="test@example.com",
        hashed_password="hashedpassword"
    )
    test_db.add(db_user)
    await test_db.commit()
    update_data = {"first_name": "John", "last_name": "Doe"}
    response = client.put(f"/users/{db_user.id}", json=update_data)
    assert response.status_code == 200
    updated_user = response.json()
    assert updated_user["first_name"] == update_data["first_name"]
    assert updated_user["last_name"] == update_data["last_name"]

@pytest.mark.asyncio
async def test_delete_user(client: TestClient, test_db: AsyncSession):
    user_repo = UserRepository(test_db)
    db_user = UserInDB(
        username="testuser",
        email="test@example.com",
        hashed_password="hashedpassword"
    )
    test_db.add(db_user)
    await test_db.commit()
    response = client.delete(f"/users/{db_user.id}")
    assert response.status_code == 204