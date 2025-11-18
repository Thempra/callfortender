# app/api/router.py

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List
from ..services.call_processing_service import CallProcessingService
from ..models.user_model import UserCreate, User, UserInDB
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
async def read_users(skip: int = 0, limit: int = 10, call_service: CallProcessingService = Depends(get_call_processing_service)):
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
async def read_user(user_id: int, call_service: CallProcessingService = Depends(get_call_processing_service)):
    """
    Retrieve a user by ID.

    Args:
        user_id (int): The ID of the user to retrieve.
        call_service (CallProcessingService): Dependency injected service for call processing.

    Returns:
        User: The retrieved user data.
    """
    try:
        return await call_service.get_user_by_id(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/users/{user_id}", response_model=User)
async def update_user(user_id: int, user_update: UserUpdate, call_service: CallProcessingService = Depends(get_call_processing_service)):
    """
    Update an existing user.

    Args:
        user_id (int): The ID of the user to update.
        user_update (UserUpdate): The data to update the user with.
        call_service (CallProcessingService): Dependency injected service for call processing.

    Returns:
        User: The updated user data.
    """
    try:
        return await call_service.update_user(user_id, user_update)
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# app/services/call_processing_service.py

from typing import List
from ..repositories.user_repository import UserRepository
from ..models.user_model import UserCreate, UserUpdate, UserInDB

class CallProcessingService:
    def __init__(self, user_repo: UserRepository):
        """
        Initialize the CallProcessingService with a UserRepository.

        Args:
            user_repo (UserRepository): The repository for user operations.
        """
        self.user_repo = user_repo

    async def create_user(self, user: UserCreate) -> UserInDB:
        """
        Create a new user.

        Args:
            user (UserCreate): The user data to be created.

        Returns:
            UserInDB: The created user data.
        """
        return await self.user_repo.create(user)

    async def get_users(self, skip: int = 0, limit: int = 10) -> List[UserInDB]:
        """
        Retrieve a list of users.

        Args:
            skip (int): Number of records to skip.
            limit (int): Maximum number of records to return.

        Returns:
            List[UserInDB]: A list of user data.
        """
        return await self.user_repo.get_all(skip, limit)

    async def get_user_by_id(self, user_id: int) -> UserInDB:
        """
        Retrieve a user by ID.

        Args:
            user_id (int): The ID of the user to retrieve.

        Returns:
            UserInDB: The retrieved user data.
        """
        return await self.user_repo.get_by_id(user_id)

    async def update_user(self, user_id: int, user_update: UserUpdate) -> UserInDB:
        """
        Update an existing user.

        Args:
            user_id (int): The ID of the user to update.
            user_update (UserUpdate): The data to update the user with.

        Returns:
            UserInDB: The updated user data.
        """
        return await self.user_repo.update(user_id, user_update)

    async def delete_user(self, user_id: int) -> UserInDB:
        """
        Delete a user by ID.

        Args:
            user_id (int): The ID of the user to delete.

        Returns:
            UserInDB: The deleted user data.
        """
        return await self.user_repo.delete(user_id)


# app/repositories/user_repository.py

from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.user_model import UserCreate, UserUpdate, UserInDB

class UserRepository:
    def __init__(self, session: AsyncSession):
        """
        Initialize the UserRepository with a database session.

        Args:
            session (AsyncSession): The database session.
        """
        self.session = session

    async def create(self, user: UserCreate) -> UserInDB:
        """
        Create a new user.

        Args:
            user (UserCreate): The user data to be created.

        Returns:
            UserInDB: The created user data.
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
        return db_user

    async def get_all(self, skip: int = 0, limit: int = 10) -> List[UserInDB]:
        """
        Retrieve a list of users.

        Args:
            skip (int): Number of records to skip.
            limit (int): Maximum number of records to return.

        Returns:
            List[UserInDB]: A list of user data.
        """
        result = await self.session.execute(
            select(UserInDB).offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def get_by_id(self, user_id: int) -> UserInDB:
        """
        Retrieve a user by ID.

        Args:
            user_id (int): The ID of the user to retrieve.

        Returns:
            UserInDB: The retrieved user data.
        """
        result = await self.session.execute(
            select(UserInDB).where(UserInDB.id == user_id)
        )
        return result.scalar_one_or_none()

    async def update(self, user_id: int, user_update: UserUpdate) -> UserInDB:
        """
        Update an existing user.

        Args:
            user_id (int): The ID of the user to update.
            user_update (UserUpdate): The data to update the user with.

        Returns:
            UserInDB: The updated user data.
        """
        db_user = await self.get_by_id(user_id)
        if not db_user:
            raise ValueError("User not found")
        for key, value in user_update.dict(exclude_unset=True).items():
            setattr(db_user, key, value)
        self.session.add(db_user)
        await self.session.commit()
        await self.session.refresh(db_user)
        return db_user

    async def delete(self, user_id: int) -> UserInDB:
        """
        Delete a user by ID.

        Args:
            user_id (int): The ID of the user to delete.

        Returns:
            UserInDB: The deleted user data.
        """
        db_user = await self.get_by_id(user_id)
        if not db_user:
            raise ValueError("User not found")
        await self.session.delete(db_user)
        await self.session.commit()
        return db_user

    @staticmethod
    def _hash_password(password: str) -> str:
        """
        Hash a password.

        Args:
            password (str): The password to be hashed.

        Returns:
            str: The hashed password.
        """
        # Placeholder for actual hashing logic
        return password


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

class UserInDB(UserInDBBase, Base):
    """
    Model for user information stored in the database, including hashed password.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    first_name = Column(String)
    last_name = Column(String)
    date_of_birth = Column(Date)
    hashed_password = Column(String)


# app/dependencies.py

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from ..repositories.user_repository import UserRepository
from .database import get_session

async def get_user_repo(session: AsyncSession = Depends(get_session)) -> UserRepository:
    """
    Dependency to get a UserRepository instance.

    Args:
        session (AsyncSession): The database session.

    Returns:
        UserRepository: A repository for user operations.
    """
    return UserRepository(session)

async def get_call_processing_service(user_repo: UserRepository = Depends(get_user_repo)) -> CallProcessingService:
    """
    Dependency to get a CallProcessingService instance.

    Args:
        user_repo (UserRepository): The repository for user operations.

    Returns:
        CallProcessingService: A service for call processing.
    """
    return CallProcessingService(user_repo)


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

async def get_session() -> AsyncSession:
    """
    Dependency to get a database session.

    Yields:
        AsyncSession: A database session.
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