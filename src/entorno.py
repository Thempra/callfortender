# main.py
from fastapi import FastAPI
from app.routers import users
from app.dependencies import get_db
from sqlalchemy.ext.asyncio import AsyncSession

app = FastAPI()

@app.on_event("startup")
async def startup():
    """
    Startup event to initialize the application.
    """
    pass

@app.on_event("shutdown")
async def shutdown():
    """
    Shutdown event to clean up resources.
    """
    pass

app.include_router(users.router, prefix="/users", tags=["users"])

# app/__init__.py
from .routers import users
from .dependencies import get_db

# app/routers/users.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.user_model import UserCreate, UserUpdate, User
from ..repositories.user_repository import UserRepository
from ..services.call_processing_service import CallProcessingService

router = APIRouter()

@router.post("/", response_model=User)
async def create_user(user: UserCreate, service: CallProcessingService = Depends()):
    """
    Create a new user.

    Args:
        user (UserCreate): The user data to be created.
        service (CallProcessingService): The call processing service.

    Returns:
        User: The created user.
    """
    return await service.create_user(user)

@router.get("/{user_id}", response_model=User)
async def read_user(user_id: int, service: CallProcessingService = Depends()):
    """
    Read a user by ID.

    Args:
        user_id (int): The ID of the user to be retrieved.
        service (CallProcessingService): The call processing service.

    Returns:
        User: The retrieved user.
    """
    return await service.read_user(user_id)

@router.put("/{user_id}", response_model=User)
async def update_user(user_id: int, user: UserUpdate, service: CallProcessingService = Depends()):
    """
    Update a user by ID.

    Args:
        user_id (int): The ID of the user to be updated.
        user (UserUpdate): The data to update the user with.
        service (CallProcessingService): The call processing service.

    Returns:
        User: The updated user.
    """
    return await service.update_user(user_id, user)

@router.delete("/{user_id}", response_model=User)
async def delete_user(user_id: int, service: CallProcessingService = Depends()):
    """
    Delete a user by ID.

    Args:
        user_id (int): The ID of the user to be deleted.
        service (CallProcessingService): The call processing service.

    Returns:
        User: The deleted user.
    """
    return await service.delete_user(user_id)

# app/services/call_processing_service.py
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from ..repositories.user_repository import UserRepository
from ..models.user_model import UserCreate, UserUpdate, User

class CallProcessingService:
    def __init__(self, user_repo: UserRepository = Depends()):
        """
        Initialize the call processing service.

        Args:
            user_repo (UserRepository): The user repository.
        """
        self.user_repo = user_repo

    async def create_user(self, user: UserCreate) -> User:
        """
        Create a new user.

        Args:
            user (UserCreate): The user data to be created.

        Returns:
            User: The created user.
        """
        return await self.user_repo.create(user)

    async def read_user(self, user_id: int) -> User:
        """
        Read a user by ID.

        Args:
            user_id (int): The ID of the user to be retrieved.

        Returns:
            User: The retrieved user.
        """
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user

    async def update_user(self, user_id: int, user: UserUpdate) -> User:
        """
        Update a user by ID.

        Args:
            user_id (int): The ID of the user to be updated.
            user (UserUpdate): The data to update the user with.

        Returns:
            User: The updated user.
        """
        return await self.user_repo.update(user_id, user)

    async def delete_user(self, user_id: int) -> User:
        """
        Delete a user by ID.

        Args:
            user_id (int): The ID of the user to be deleted.

        Returns:
            User: The deleted user.
        """
        return await self.user_repo.delete(user_id)

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
            User: The created user.
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

    async def get_by_id(self, user_id: int) -> User:
        """
        Retrieve a user by ID.

        Args:
            user_id (int): The ID of the user to be retrieved.

        Returns:
            User: The retrieved user.
        """
        result = await self.session.execute(select(UserInDB).where(UserInDB.id == user_id))
        db_user = result.scalar_one_or_none()
        return User.from_orm(db_user) if db_user else None

    async def update(self, user_id: int, user: UserUpdate) -> User:
        """
        Update a user by ID.

        Args:
            user_id (int): The ID of the user to be updated.
            user (UserUpdate): The data to update the user with.

        Returns:
            User: The updated user.
        """
        db_user = await self.get_by_id(user_id)
        if not db_user:
            raise HTTPException(status_code=404, detail="User not found")
        for key, value in user.dict(exclude_unset=True).items():
            setattr(db_user, key, value)
        self.session.add(db_user)
        await self.session.commit()
        await self.session.refresh(db_user)
        return User.from_orm(db_user)

    async def delete(self, user_id: int) -> User:
        """
        Delete a user by ID.

        Args:
            user_id (int): The ID of the user to be deleted.

        Returns:
            User: The deleted user.
        """
        db_user = await self.get_by_id(user_id)
        if not db_user:
            raise HTTPException(status_code=404, detail="User not found")
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

# app/dependencies.py
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_db
from .repositories.user_repository import UserRepository
from .services.call_processing_service import CallProcessingService

def get_user_repo(session: AsyncSession = Depends(get_db)) -> UserRepository:
    """
    Dependency to get the user repository.

    Args:
        session (AsyncSession): The database session.

    Returns:
        UserRepository: The user repository.
    """
    return UserRepository(session)

def get_call_processing_service(user_repo: UserRepository = Depends(get_user_repo)) -> CallProcessingService:
    """
    Dependency to get the call processing service.

    Args:
        user_repo (UserRepository): The user repository.

    Returns:
        CallProcessingService: The call processing service.
    """
    return CallProcessingService(user_repo)

# app/database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from .models.user_model import Base

DATABASE_URL = "postgresql+asyncpg://user:password@localhost/dbname"

engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db() -> AsyncSession:
    """
    Dependency to get the database session.

    Yields:
        AsyncSession: The database session.
    """
    async with AsyncSessionLocal() as session:
        yield session

# tests/test_main.py
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_user():
    response = client.post("/users/", json={"username": "testuser", "email": "test@example.com", "password": "testpass"})
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"

def test_read_user():
    response = client.get("/users/1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1

def test_update_user():
    response = client.put("/users/1", json={"username": "updateduser"})
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "updateduser"

def test_delete_user():
    response = client.delete("/users/1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1

# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture(scope="module")
def client():
    """
    Fixture to create a test client for the application.

    Yields:
        TestClient: The test client.
    """
    with TestClient(app) as c:
        yield c