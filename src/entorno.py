# main.py
from fastapi import FastAPI
from app.routers import users
from app.dependencies import get_db
from sqlalchemy.orm import Session

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    """
    Startup event to initialize any necessary resources.
    """
    pass

@app.on_event("shutdown")
async def shutdown_event():
    """
    Shutdown event to clean up any resources.
    """
    pass

app.include_router(users.router, prefix="/users", tags=["users"])

# app/__init__.py
from .routers import users
from .dependencies import get_db

# app/routers/users.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..schemas import UserCreate, User
from ..crud import create_user, get_users, get_user_by_id, update_user, delete_user
from ..dependencies import get_db

router = APIRouter()

@router.post("/", response_model=User)
def create_new_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    Create a new user.

    Args:
        user (UserCreate): The user data to be created.
        db (Session): The database session.

    Returns:
        User: The created user data.
    """
    db_user = create_user(db=db, user=user)
    return db_user

@router.get("/", response_model=list[User])
def read_users(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    """
    Retrieve a list of users.

    Args:
        skip (int): The number of records to skip.
        limit (int): The maximum number of records to return.
        db (Session): The database session.

    Returns:
        List[User]: A list of user data.
    """
    users = get_users(db, skip=skip, limit=limit)
    return users

@router.get("/{user_id}", response_model=User)
def read_user(user_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a single user by ID.

    Args:
        user_id (int): The ID of the user to retrieve.
        db (Session): The database session.

    Returns:
        User: The retrieved user data.
    """
    db_user = get_user_by_id(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.put("/{user_id}", response_model=User)
def update_existing_user(user_id: int, user: UserCreate, db: Session = Depends(get_db)):
    """
    Update an existing user.

    Args:
        user_id (int): The ID of the user to update.
        user (UserCreate): The updated user data.
        db (Session): The database session.

    Returns:
        User: The updated user data.
    """
    db_user = update_user(db=db, user_id=user_id, user=user)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.delete("/{user_id}", response_model=User)
def delete_existing_user(user_id: int, db: Session = Depends(get_db)):
    """
    Delete an existing user.

    Args:
        user_id (int): The ID of the user to delete.
        db (Session): The database session.

    Returns:
        User: The deleted user data.
    """
    db_user = delete_user(db=db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

# app/schemas.py
from pydantic import BaseModel, EmailStr, Field
from datetime import date
from typing import Optional

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
from sqlalchemy.orm import Session
from .models import User as UserModel
from .schemas import UserCreate, UserUpdate
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_user(db: Session, user: UserCreate):
    """
    Create a new user in the database.

    Args:
        db (Session): The database session.
        user (UserCreate): The user data to be created.

    Returns:
        UserModel: The created user data.
    """
    hashed_password = pwd_context.hash(user.password)
    db_user = UserModel(
        username=user.username,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        date_of_birth=user.date_of_birth,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_users(db: Session, skip: int = 0, limit: int = 10):
    """
    Retrieve a list of users from the database.

    Args:
        db (Session): The database session.
        skip (int): The number of records to skip.
        limit (int): The maximum number of records to return.

    Returns:
        List[UserModel]: A list of user data.
    """
    return db.query(UserModel).offset(skip).limit(limit).all()

def get_user_by_id(db: Session, user_id: int):
    """
    Retrieve a single user by ID from the database.

    Args:
        db (Session): The database session.
        user_id (int): The ID of the user to retrieve.

    Returns:
        UserModel: The retrieved user data.
    """
    return db.query(UserModel).filter(UserModel.id == user_id).first()

def update_user(db: Session, user_id: int, user: UserUpdate):
    """
    Update an existing user in the database.

    Args:
        db (Session): The database session.
        user_id (int): The ID of the user to update.
        user (UserUpdate): The updated user data.

    Returns:
        UserModel: The updated user data.
    """
    db_user = get_user_by_id(db, user_id=user_id)
    if db_user is None:
        return None
    for key, value in user.dict(exclude_unset=True).items():
        setattr(db_user, key, value)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def delete_user(db: Session, user_id: int):
    """
    Delete an existing user from the database.

    Args:
        db (Session): The database session.
        user_id (int): The ID of the user to delete.

    Returns:
        UserModel: The deleted user data.
    """
    db_user = get_user_by_id(db, user_id=user_id)
    if db_user is None:
        return None
    db.delete(db_user)
    db.commit()
    return db_user

# app/models.py
from sqlalchemy import Column, Integer, String, Date
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
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
    hashed_password = Column(String)

# app/dependencies.py
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_db

def get_user_repo(session: AsyncSession = Depends(get_db)):
    """
    Dependency to get the user repository.

    Args:
        session (AsyncSession): The database session.

    Returns:
        UserRepository: The user repository.
    """
    from .repositories.user_repository import UserRepository
    return UserRepository(session)

def get_call_processing_service(user_repo: UserRepository = Depends(get_user_repo)):
    """
    Dependency to get the call processing service.

    Args:
        user_repo (UserRepository): The user repository.

    Returns:
        CallProcessingService: The call processing service.
    """
    from .services.call_processing_service import CallProcessingService
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
    """
    Configuration settings for the application.
    """
    database_hostname: str = "localhost"
    database_port: str = "5432"
    database_password: str = "password"
    database_name: str = "fastapi_db"
    database_username: str = "postgres"

settings = Settings()

# tests/test_main.py
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_user():
    """
    Test creating a new user.
    """
    response = client.post(
        "/users/",
        json={"username": "testuser", "email": "test@example.com", "password": "testpass"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"

def test_read_users():
    """
    Test retrieving a list of users.
    """
    response = client.get("/users/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_read_user():
    """
    Test retrieving a single user by ID.
    """
    response = client.get("/users/1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1

def test_update_user():
    """
    Test updating an existing user.
    """
    response = client.put(
        "/users/1",
        json={"username": "updateduser", "email": "updated@example.com", "password": "updatedpass"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "updateduser"
    assert data["email"] == "updated@example.com"

def test_delete_user():
    """
    Test deleting an existing user.
    """
    response = client.delete("/users/1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1

# Dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

# docker-compose.yml
version: '3.9'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    depends_on:
      - db

  db:
    image: postgres:13
    environment:
      POSTGRES_DB: fastapi_db
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    volumes:
      - db_data:/var/lib/postgresql/data

volumes:
  db_data:

# requirements.txt
fastapi[all]
uvicorn[standard]
sqlalchemy
asyncpg
passlib
bcrypt
pydantic
pytest