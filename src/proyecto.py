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

@router.put("/users/{user_id}", response_model=User)
async def update_user(user_id: int, user_update: UserUpdate, call_service: CallProcessingService = Depends(get_call_processing_service)):
    """
    Update an existing user.

    Args:
        user_id (int): The ID of the user to be updated.
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
    Delete a user.

    Args:
        user_id (int): The ID of the user to be deleted.
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
from ..models.user_model import UserCreate, UserUpdate, UserInDB, User
from ..repositories.user_repository import UserRepository
from passlib.context import CryptContext

class CallProcessingService:
    def __init__(self, user_repo: UserRepository):
        """
        Initialize the CallProcessingService with a UserRepository.

        Args:
            user_repo (UserRepository): The repository for user data.
        """
        self.user_repo = user_repo
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    async def create_user(self, user: UserCreate) -> UserInDB:
        """
        Create a new user.

        Args:
            user (UserCreate): The user data to be created.

        Returns:
            UserInDB: The created user data.
        """
        hashed_password = self.pwd_context.hash(user.password)
        db_user = UserInDB(**user.dict(), hashed_password=hashed_password)
        return await self.user_repo.create(db_user)

    async def get_users(self, skip: int, limit: int) -> List[User]:
        """
        Retrieve a list of users.

        Args:
            skip (int): Number of records to skip.
            limit (int): Maximum number of records to return.

        Returns:
            List[User]: A list of user data.
        """
        db_users = await self.user_repo.get_all(skip, limit)
        return [User.from_orm(user) for user in db_users]

    async def update_user(self, user_id: int, user_update: UserUpdate) -> UserInDB:
        """
        Update an existing user.

        Args:
            user_id (int): The ID of the user to be updated.
            user_update (UserUpdate): The data to update the user with.

        Returns:
            UserInDB: The updated user data.
        """
        db_user = await self.user_repo.get_by_id(user_id)
        if not db_user:
            raise ValueError("User not found")
        for field, value in user_update.dict(exclude_unset=True).items():
            setattr(db_user, field, value)
        return await self.user_repo.update(db_user)

    async def delete_user(self, user_id: int) -> UserInDB:
        """
        Delete a user.

        Args:
            user_id (int): The ID of the user to be deleted.

        Returns:
            UserInDB: The deleted user data.
        """
        db_user = await self.user_repo.get_by_id(user_id)
        if not db_user:
            raise ValueError("User not found")
        return await self.user_repo.delete(db_user)


# app/repositories/user_repository.py

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from .user_repository import UserRepository
from .services.call_processing_service import CallProcessingService

DATABASE_URL = "postgresql+asyncpg://user:password@localhost/dbname"

engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_session() -> AsyncSession:
    """
    Dependency to get the database session.

    Yields:
        AsyncSession: The database session.
    """
    async with AsyncSessionLocal() as session:
        yield session

def get_user_repository(session: AsyncSession = Depends(get_session)) -> UserRepository:
    """
    Dependency to get the user repository.

    Args:
        session (AsyncSession): The database session.

    Returns:
        UserRepository: The user repository.
    """
    return UserRepository(session)

def get_call_processing_service(user_repo: UserRepository = Depends(get_user_repository)) -> CallProcessingService:
    """
    Dependency to get the call processing service.

    Args:
        user_repo (UserRepository): The user repository.

    Returns:
        CallProcessingService: The call processing service.
    """
    return CallProcessingService(user_repo)


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


class UserInDB(UserInDBBase):
    """
    Model for user information stored in the database, including hashed password.
    """
    hashed_password: str