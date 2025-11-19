# main.py
from fastapi import FastAPI
from app.api.routers import user_router
from app.database import engine, Base

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(user_router.router, prefix="/users", tags=["users"])


# app/api/routers/user_router.py
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user_model import UserCreate, UserUpdate, User
from app.repositories.user_repository import UserRepository
from app.dependencies import get_user_repo

router = APIRouter()

@router.post("/", response_model=User)
async def create_user(user: UserCreate, user_repo: UserRepository = Depends(get_user_repo)):
    return await user_repo.create(user)

@router.get("/{user_id}", response_model=User)
async def read_user(user_id: int, user_repo: UserRepository = Depends(get_user_repo)):
    db_user = await user_repo.get_by_id(user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.put("/{user_id}", response_model=User)
async def update_user(user_id: int, user_update: UserUpdate, user_repo: UserRepository = Depends(get_user_repo)):
    try:
        return await user_repo.update(user_id, user_update)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/{user_id}", response_model=User)
async def delete_user(user_id: int, user_repo: UserRepository = Depends(get_user_repo)):
    try:
        return await user_repo.delete(user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# app/models/user_model.py
from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from datetime import date
from sqlalchemy import Column, Integer, String, Date
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class UserBase(BaseModel):
    """
    Base model for user information.
    """
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[date] = None

class UserCreate(UserBase):
    """
    Model for creating a new user.
    """
    password: str = Field(..., min_length=8)

class UserUpdate(UserBase):
    """
    Model for updating an existing user.
    """

class UserInDBBase(UserBase):
    id: int

    class Config:
        orm_mode = True

class User(UserInDBBase):
    """
    Model for user information returned to the client.
    """

class UserInDB(UserInDBBase):
    """
    Model for user information stored in the database, including hashed password.
    """
    hashed_password: str


# app/repositories/user_repository.py
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.user_model import UserInDB, UserCreate, UserUpdate, User
from .base_repository import BaseRepository

class UserRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        """
        Initialize the user repository.

        Args:
            session (AsyncSession): The database session.
        """
        super().__init__(session)

    async def create(self, user: UserCreate) -> User:
        """
        Create a new user.

        Args:
            user (UserCreate): The user data to be created.

        Returns:
            User: The created user data.
        """
        db_user = UserInDB(
            username=user.username,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            date_of_birth=user.date_of_birth,
            hashed_password=self._hash_password(user.password)
        )
        self.session.add(db_user)
        await self.session.commit()
        await self.session.refresh(db_user)
        return User.from_orm(db_user)

    async def get_all(self, skip: int = 0, limit: int = 10) -> list[User]:
        """
        Retrieve a list of users.

        Args:
            skip (int): Number of records to skip.
            limit (int): Maximum number of records to return.

        Returns:
            List[User]: A list of user data.
        """
        result = await self.session.execute(select(UserInDB).offset(skip).limit(limit))
        return [User.from_orm(user) for user in result.scalars().all()]

    async def get_by_id(self, user_id: int) -> User:
        """
        Retrieve a user by ID.

        Args:
            user_id (int): The ID of the user to retrieve.

        Returns:
            User: The retrieved user data.
        """
        result = await self.session.execute(select(UserInDB).where(UserInDB.id == user_id))
        db_user = result.scalar_one_or_none()
        if not db_user:
            raise ValueError(f"User with id {user_id} not found")
        return User.from_orm(db_user)

    async def update(self, user_id: int, user_update: UserUpdate) -> User:
        """
        Update an existing user.

        Args:
            user_id (int): The ID of the user to update.
            user_update (UserUpdate): The data to update the user with.

        Returns:
            User: The updated user data.
        """
        db_user = await self.get_by_id(user_id)
        for key, value in user_update.dict(exclude_unset=True).items():
            setattr(db_user, key, value)
        self.session.add(db_user)
        await self.session.commit()
        await self.session.refresh(db_user)
        return User.from_orm(db_user)

    async def delete(self, user_id: int) -> User:
        """
        Delete a user by ID.

        Args:
            user_id (int): The ID of the user to delete.

        Returns:
            User: The deleted user data.
        """
        db_user = await self.get_by_id(user_id)
        await self.session.delete(db_user)
        await self.session.commit()
        return User.from_orm(db_user)

    def _hash_password(self, password: str) -> str:
        """
        Hash a password.

        Args:
            password (str): The password to hash.

        Returns:
            str: The hashed password.
        """
        # Placeholder for actual hashing logic
        return password


# app/repositories/base_repository.py
from sqlalchemy.ext.asyncio import AsyncSession

class BaseRepository:
    def __init__(self, session: AsyncSession):
        """
        Initialize the base repository.

        Args:
            session (AsyncSession): The database session.
        """
        self.session = session


# app/database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from .config import settings

DATABASE_URL = f"postgresql+asyncpg://{settings.database_username}:{settings.database_password}@{settings.database_hostname}:{settings.database_port}/{settings.database_name}"

engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db():
    """
    Dependency to get the database session.

    Yields:
        AsyncSession: The database session.
    """
    async with AsyncSessionLocal() as session:
        yield session


# app/config.py
from pydantic import BaseSettings

class Settings(BaseSettings):
    database_hostname: str
    database_port: str
    database_password: str
    database_name: str
    database_username: str

    class Config:
        env_file = ".env"

settings = Settings()


# app/dependencies.py
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_db
from .repositories.user_repository import UserRepository

def get_user_repo(session: AsyncSession = Depends(get_db)) -> UserRepository:
    """
    Dependency to get the user repository.

    Args:
        session (AsyncSession): The database session.

    Returns:
        UserRepository: The user repository.
    """
    return UserRepository(session)


# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.database import Base, DATABASE_URL
from app.main import app

SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

@pytest.fixture(scope="module")
async def test_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture(scope="module")
def client(test_db):
    app.dependency_overrides[get_db] = get_test_db
    yield TestClient(app)
    del app.dependency_overrides[get_db]

async def get_test_db():
    async with TestingSessionLocal() as session:
        yield session


# tests/test_users.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user_model import UserCreate, UserUpdate

@pytest.mark.asyncio
async def test_create_user(client: TestClient):
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "securepassword"
    }
    response = client.post("/users/", json=user_data)
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == user_data["username"]
    assert data["email"] == user_data["email"]

@pytest.mark.asyncio
async def test_read_user(client: TestClient, test_db):
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "securepassword"
    }
    response = client.post("/users/", json=user_data)
    assert response.status_code == 200
    data = response.json()
    user_id = data["id"]
    response = client.get(f"/users/{user_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == user_data["username"]

@pytest.mark.asyncio
async def test_update_user(client: TestClient, test_db):
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "securepassword"
    }
    response = client.post("/users/", json=user_data)
    assert response.status_code == 200
    data = response.json()
    user_id = data["id"]
    update_data = {
        "first_name": "John",
        "last_name": "Doe"
    }
    response = client.put(f"/users/{user_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["first_name"] == update_data["first_name"]
    assert data["last_name"] == update_data["last_name"]

@pytest.mark.asyncio
async def test_delete_user(client: TestClient, test_db):
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "securepassword"
    }
    response = client.post("/users/", json=user_data)
    assert response.status_code == 200
    data = response.json()
    user_id = data["id"]
    response = client.delete(f"/users/{user_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == user_data["username"]