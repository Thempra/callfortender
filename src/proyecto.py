# app/api/router.py

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List
from ..services.call_processing_service import CallProcessingService
from ..models.user_model import UserCreate, User, UserUpdate
from ..dependencies import get_call_processing_service

router = APIRouter()

@router.post("/users/", response_model=User)
async def create_user(user: UserCreate, call_service: CallProcessingService = Depends(get_call_processing_service)):
    """
    Create a new user.

    Args:
        user (UserCreate): The user data to be created.
        call_service (CallProcessingService): Dependency injected service for call processing.

    Returns:
        User: The created user data.
    """
    try:
        return await call_service.create_user(user)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/users/", response_model=List[User])
async def get_users(skip: int = 0, limit: int = 10, call_service: CallProcessingService = Depends(get_call_processing_service)):
    """
    Retrieve a list of users.

    Args:
        skip (int): Number of records to skip.
        limit (int): Maximum number of records to return.
        call_service (CallProcessingService): Dependency injected service for call processing.

    Returns:
        List[User]: A list of user data.
    """
    try:
        return await call_service.get_users(skip, limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/users/{user_id}", response_model=User)
async def get_user(user_id: int, call_service: CallProcessingService = Depends(get_call_processing_service)):
    """
    Retrieve a user by ID.

    Args:
        user_id (int): The ID of the user to retrieve.
        call_service (CallProcessingService): Dependency injected service for call processing.

    Returns:
        User: The retrieved user data.
    """
    try:
        return await call_service.get_user(user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/users/{user_id}", response_model=User)
async def update_user(user_id: int, user_update: UserUpdate, call_service: CallProcessingService = Depends(get_call_processing_service)):
    """
    Update a user by ID.

    Args:
        user_id (int): The ID of the user to update.
        user_update (UserUpdate): The data to update the user with.
        call_service (CallProcessingService): Dependency injected service for call processing.

    Returns:
        User: The updated user data.
    """
    try:
        return await call_service.update_user(user_id, user_update)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/users/{user_id}", response_model=User)
async def delete_user(user_id: int, call_service: CallProcessingService = Depends(get_call_processing_service)):
    """
    Delete a user by ID.

    Args:
        user_id (int): The ID of the user to delete.
        call_service (CallProcessingService): Dependency injected service for call processing.

    Returns:
        User: The deleted user data.
    """
    try:
        return await call_service.delete_user(user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# app/services/call_processing_service.py

from typing import List
from ..repositories.user_repository import UserRepository
from ..models.user_model import UserCreate, UserUpdate, User

class CallProcessingService:
    def __init__(self, user_repo: UserRepository):
        """
        Initialize the CallProcessingService with a UserRepository.

        Args:
            user_repo (UserRepository): The repository for user operations.
        """
        self.user_repo = user_repo

    async def create_user(self, user: UserCreate) -> User:
        """
        Create a new user.

        Args:
            user (UserCreate): The user data to be created.

        Returns:
            User: The created user data.
        """
        return await self.user_repo.create(user)

    async def get_users(self, skip: int = 0, limit: int = 10) -> List[User]:
        """
        Retrieve a list of users.

        Args:
            skip (int): Number of records to skip.
            limit (int): Maximum number of records to return.

        Returns:
            List[User]: A list of user data.
        """
        return await self.user_repo.get_all(skip, limit)

    async def get_user(self, user_id: int) -> User:
        """
        Retrieve a user by ID.

        Args:
            user_id (int): The ID of the user to retrieve.

        Returns:
            User: The retrieved user data.
        """
        return await self.user_repo.get_by_id(user_id)

    async def update_user(self, user_id: int, user_update: UserUpdate) -> User:
        """
        Update a user by ID.

        Args:
            user_id (int): The ID of the user to update.
            user_update (UserUpdate): The data to update the user with.

        Returns:
            User: The updated user data.
        """
        return await self.user_repo.update(user_id, user_update)

    async def delete_user(self, user_id: int) -> User:
        """
        Delete a user by ID.

        Args:
            user_id (int): The ID of the user to delete.

        Returns:
            User: The deleted user data.
        """
        return await self.user_repo.delete(user_id)


# app/repositories/user_repository.py

from sqlalchemy import select
from typing import List
from ..models.user_model import UserCreate, UserUpdate, UserInDB, User
from .base_repository import BaseRepository

class UserRepository(BaseRepository):
    def __init__(self, session):
        """
        Initialize the UserRepository with a database session.

        Args:
            session: The database session.
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
        db_user = UserInDB(**user.dict(), hashed_password=self._hash_password(user.password))
        self.session.add(db_user)
        await self.session.commit()
        await self.session.refresh(db_user)
        return db_user

    async def get_all(self, skip: int = 0, limit: int = 10) -> List[User]:
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
        Update a user by ID.

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
        Initialize the BaseRepository with a database session.

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
        user_repo (UserRepository): The repository for user operations.

    Returns:
        CallProcessingService: The call processing service.
    """
    return CallProcessingService(user_repo)


# app/database.py

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from .config import settings

DATABASE_URL = f"postgresql+asyncpg://{settings.database_username}:{settings.database_password}@{settings.database_host}/{settings.database_name}"

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
    database_host: str
    database_name: str
    database_username: str
    database_password: str

    class Config:
        env_file = ".env"

settings = Settings()