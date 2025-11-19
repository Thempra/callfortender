# main.py
from fastapi import FastAPI
from app.routers import users
from app.database import create_tables

app = FastAPI()

@app.on_event("startup")
async def startup():
    await create_tables()

app.include_router(users.router, prefix="/users", tags=["users"])


# app/__init__.py
# Source package


# app/routers/users.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.user_model import UserCreate, UserUpdate, User
from ..repositories.user_repository import UserRepository
from ..dependencies import get_user_repo

router = APIRouter()

@router.post("/", response_model=User)
async def create_user(user: UserCreate, user_repo: UserRepository = Depends(get_user_repo)):
    return await user_repo.create(user)

@router.get("/{user_id}", response_model=User)
async def read_user(user_id: int, user_repo: UserRepository = Depends(get_user_repo)):
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.put("/{user_id}", response_model=User)
async def update_user(user_id: int, user_update: UserUpdate, user_repo: UserRepository = Depends(get_user_repo)):
    user = await user_repo.update(user_id, user_update)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.delete("/{user_id}", response_model=User)
async def delete_user(user_id: int, user_repo: UserRepository = Depends(get_user_repo)):
    user = await user_repo.delete(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# app/models/user_model.py
from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from datetime import date

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
    """
    Base model for user information stored in the database.
    """
    id: int

    class Config:
        orm_mode = True

class User(UserInDBBase):
    """
    Model for user information returned to the client.
    """


# app/repositories/user_repository.py
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.user_model import UserCreate, UserUpdate, User, UserInDB
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

async def create_tables():
    """
    Create all tables in the database.
    """
    from .models.user_model import UserInDB
    async with engine.begin() as conn:
        await conn.run_sync(UserInDB.metadata.create_all)


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
from .database import get_db
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


# app/services/call_processing_service.py
from .repositories.user_repository import UserRepository

class CallProcessingService:
    def __init__(self, user_repo: UserRepository):
        """
        Initialize the call processing service.

        Args:
            user_repo (UserRepository): The user repository.
        """
        self.user_repo = user_repo


# tests/conftest.py
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import engine, AsyncSessionLocal
from app.models.user_model import UserInDB

@pytest.fixture(scope="session")
async def async_session():
    """
    Fixture to create a new database session for each test.

    Yields:
        AsyncSession: The database session.
    """
    async with engine.begin() as conn:
        await conn.run_sync(UserInDB.metadata.create_all)
    async with AsyncSessionLocal() as session:
        yield session
    async with engine.begin() as conn:
        await conn.run_sync(UserInDB.metadata.drop_all)


# tests/test_users.py
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user_model import UserCreate, UserUpdate
from app.repositories.user_repository import UserRepository

@pytest.fixture(scope="function")
async def user_repo(async_session: AsyncSession) -> UserRepository:
    """
    Fixture to create a new user repository for each test.

    Args:
        async_session (AsyncSession): The database session.

    Returns:
        UserRepository: The user repository.
    """
    return UserRepository(async_session)

@pytest.mark.asyncio
async def test_create_user(user_repo: UserRepository):
    """
    Test creating a new user.
    """
    user = await user_repo.create(UserCreate(username="testuser", email="test@example.com", password="password"))
    assert user.username == "testuser"
    assert user.email == "test@example.com"

@pytest.mark.asyncio
async def test_read_user(user_repo: UserRepository):
    """
    Test reading a user by ID.
    """
    created_user = await user_repo.create(UserCreate(username="testuser", email="test@example.com", password="password"))
    read_user = await user_repo.get_by_id(created_user.id)
    assert read_user.username == "testuser"
    assert read_user.email == "test@example.com"

@pytest.mark.asyncio
async def test_update_user(user_repo: UserRepository):
    """
    Test updating a user.
    """
    created_user = await user_repo.create(UserCreate(username="testuser", email="test@example.com", password="password"))
    updated_user = await user_repo.update(created_user.id, UserUpdate(first_name="John", last_name="Doe"))
    assert updated_user.first_name == "John"
    assert updated_user.last_name == "Doe"

@pytest.mark.asyncio
async def test_delete_user(user_repo: UserRepository):
    """
    Test deleting a user.
    """
    created_user = await user_repo.create(UserCreate(username="testuser", email="test@example.com", password="password"))
    deleted_user = await user_repo.delete(created_user.id)
    assert deleted_user.username == "testuser"
    assert deleted_user.email == "test@example.com"