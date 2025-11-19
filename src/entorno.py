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
from fastapi import HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from ..repositories.user_repository import UserRepository
from ..models.user_model import UserCreate, UserUpdate, User

class CallProcessingService:
    def __init__(self, user_repo: UserRepository = Depends(UserRepository)):
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
        existing_user = await self.user_repo.get_by_id(user_id)
        if not existing_user:
            raise HTTPException(status_code=404, detail="User not found")
        return await self.user_repo.update(user_id, user)

    async def delete_user(self, user_id: int) -> User:
        """
        Delete a user by ID.

        Args:
            user_id (int): The ID of the user to be deleted.

        Returns:
            User: The deleted user.
        """
        existing_user = await self.user_repo.get_by_id(user_id)
        if not existing_user:
            raise HTTPException(status_code=404, detail="User not found")
        return await self.user_repo.delete(user_id)

# app/repositories/user_repository.py
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.user_model import UserCreate, UserUpdate, User

class UserRepository:
    def __init__(self, session: AsyncSession = Depends(get_db)):
        """
        Initialize the user repository.

        Args:
            session (AsyncSession): The database session.
        """
        self.session = session

    async def create(self, user: UserCreate) -> User:
        """
        Create a new user.

        Args:
            user (UserCreate): The user data to be created.

        Returns:
            User: The created user.
        """
        db_user = User(**user.dict())
        self.session.add(db_user)
        await self.session.commit()
        await self.session.refresh(db_user)
        return db_user

    async def get_by_id(self, user_id: int) -> User:
        """
        Get a user by ID.

        Args:
            user_id (int): The ID of the user to be retrieved.

        Returns:
            User: The retrieved user.
        """
        result = await self.session.get(User, user_id)
        return result

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
        await self.session.commit()
        await self.session.refresh(db_user)
        return db_user

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
        return db_user

# app/models/user_model.py
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)

class UserCreate(BaseModel):
    name: str
    email: str

class UserUpdate(BaseModel):
    name: str = None
    email: str = None