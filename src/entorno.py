# requirements.txt
fastapi>=0.78.0
uvicorn[standard]>=0.17.6
sqlalchemy>=1.4.39
asyncpg>=0.25.0
pydantic[email]>=1.10.2
pytest>=7.1.2
coverage>=6.4.1
redis>=4.1.4

# docker-compose.yml
version: '3.8'

services:
  app:
    build: .
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    volumes:
      - .:/code
    ports:
      - "8000:8000"
    depends_on:
      - db
      - redis

  db:
    image: postgres:13
    environment:
      POSTGRES_USER: ${DATABASE_USERNAME}
      POSTGRES_PASSWORD: ${DATABASE_PASSWORD}
      POSTGRES_DB: ${DATABASE_NAME}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:6.2
    ports:
      - "6379:6379"

volumes:
  postgres_data:

# Dockerfile
FROM python:3.11-slim

WORKDIR /code

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# app/main.py
from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.routers import users

app = FastAPI()

@app.on_event("startup")
async def startup():
    """
    Startup event to initialize any necessary resources.
    """
    pass

@app.on_event("shutdown")
async def shutdown():
    """
    Shutdown event to clean up any resources.
    """
    pass

app.include_router(users.router, prefix="/users", tags=["users"])

# app/routers/users.py
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas import UserCreate, User
from app.crud import create_user, get_user_by_id, update_user, delete_user
from app.dependencies import get_db

router = APIRouter()

@router.post("/", response_model=User)
async def create_new_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    Create a new user.

    Args:
        user (UserCreate): The user data to create.
        db (AsyncSession): The database session.

    Returns:
        User: The created user.
    """
    db_user = await create_user(db=db, user=user)
    return db_user

@router.get("/{user_id}", response_model=User)
async def read_user(user_id: int, db: AsyncSession = Depends(get_db)):
    """
    Get a user by ID.

    Args:
        user_id (int): The ID of the user to retrieve.
        db (AsyncSession): The database session.

    Returns:
        User: The retrieved user.

    Raises:
        HTTPException: If the user is not found.
    """
    db_user = await get_user_by_id(db=db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.put("/{user_id}", response_model=User)
async def update_existing_user(user_id: int, user_update: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    Update an existing user.

    Args:
        user_id (int): The ID of the user to update.
        user_update (UserCreate): The updated user data.
        db (AsyncSession): The database session.

    Returns:
        User: The updated user.

    Raises:
        HTTPException: If the user is not found.
    """
    db_user = await update_user(db=db, user_id=user_id, user_update=user_update)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.delete("/{user_id}", response_model=User)
async def delete_existing_user(user_id: int, db: AsyncSession = Depends(get_db)):
    """
    Delete an existing user.

    Args:
        user_id (int): The ID of the user to delete.
        db (AsyncSession): The database session.

    Returns:
        User: The deleted user.

    Raises:
        HTTPException: If the user is not found.
    """
    db_user = await delete_user(db=db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

# app/schemas.py
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

# app/crud.py
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import UserInDB, UserCreate, UserUpdate, User
from app.repositories.user_repository import UserRepository

async def create_user(db: AsyncSession, user: UserCreate) -> User:
    """
    Create a new user.

    Args:
        db (AsyncSession): The database session.
        user (UserCreate): The user data to create.

    Returns:
        User: The created user.
    """
    user_repo = UserRepository(session=db)
    return await user_repo.create(user=user)

async def get_user_by_id(db: AsyncSession, user_id: int) -> User:
    """
    Get a user by ID.

    Args:
        db (AsyncSession): The database session.
        user_id (int): The ID of the user to retrieve.

    Returns:
        User: The retrieved user.
    """
    user_repo = UserRepository(session=db)
    return await user_repo.get_by_id(user_id=user_id)

async def update_user(db: AsyncSession, user_id: int, user_update: UserUpdate) -> User:
    """
    Update an existing user.

    Args:
        db (AsyncSession): The database session.
        user_id (int): The ID of the user to update.
        user_update (UserUpdate): The updated user data.

    Returns:
        User: The updated user.
    """
    user_repo = UserRepository(session=db)
    return await user_repo.update(user_id=user_id, user_update=user_update)

async def delete_user(db: AsyncSession, user_id: int) -> User:
    """
    Delete an existing user.

    Args:
        db (AsyncSession): The database session.
        user_id (int): The ID of the user to delete.

    Returns:
        User: The deleted user.
    """
    user_repo = UserRepository(session=db)
    return await user_repo.delete(user_id=user_id)

# app/models.py
from typing import Optional
from sqlalchemy import Column, Integer, String, Date
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class UserInDB(Base):
    """
    Model for user information stored in the database.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    email = Column(String(255), unique=True, index=True)
    first_name = Column(String(100))
    last_name = Column(String(100))
    date_of_birth = Column(Date)
    hashed_password = Column(String(255))

# app/repositories/user_repository.py
from sqlalchemy.ext.asyncio import AsyncSession
from ..models import UserInDB, UserCreate, UserUpdate, User
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
        Get a user by ID.

        Args:
            user_id (int): The ID of the user to retrieve.

        Returns:
            User: The retrieved user.
        """
        result = await self.session.get(UserInDB, user_id)
        return User.from_orm(result) if result else None

    async def update(self, user_id: int, user_update: UserUpdate) -> User:
        """
        Update an existing user.

        Args:
            user_id (int): The ID of the user to update.
            user_update (UserUpdate): The updated user data.

        Returns:
            User: The updated user.
        """
        db_user = await self.session.get(UserInDB, user_id)
        if db_user is None:
            return None
        for key, value in user_update.dict(exclude_unset=True).items():
            setattr(db_user, key, value)
        await self.session.commit()
        await self.session.refresh(db_user)
        return User.from_orm(db_user)

    async def delete(self, user_id: int) -> User:
        """
        Delete an existing user.

        Args:
            user_id (int): The ID of the user to delete.

        Returns:
            User: The deleted user.
        """
        db_user = await self.session.get(UserInDB, user_id)
        if db_user is None:
            return None
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