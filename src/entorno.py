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
from ..schemas import UserCreate, User
from ..services.user_service import UserService

router = APIRouter()

@router.post("/", response_model=User)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    Create a new user.

    Args:
        user (UserCreate): The user data to be created.
        db (AsyncSession): The database session.

    Returns:
        User: The created user data.
    """
    service = UserService(db)
    return await service.create_user(user)

@router.get("/{user_id}", response_model=User)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    """
    Get a user by ID.

    Args:
        user_id (int): The ID of the user to retrieve.
        db (AsyncSession): The database session.

    Returns:
        User: The retrieved user data.
    """
    service = UserService(db)
    user = await service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# app/schemas.py
from pydantic import BaseModel, EmailStr, Field
from datetime import date

class UserBase(BaseModel):
    """
    Base model for user information.
    """
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    first_name: str | None = None
    last_name: str | None = None
    date_of_birth: date | None = None

class UserCreate(UserBase):
    """
    Model for creating a new user.
    """
    password: str = Field(..., min_length=8)

class User(UserBase):
    """
    Model for user information returned to the client.
    """
    id: int

    class Config:
        orm_mode = True

# app/services/user_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.user_model import UserInDB, UserCreate
from ..schemas import User
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserService:
    def __init__(self, db: AsyncSession):
        """
        Initialize the user service.

        Args:
            db (AsyncSession): The database session.
        """
        self.db = db

    async def create_user(self, user: UserCreate) -> User:
        """
        Create a new user.

        Args:
            user (UserCreate): The user data to be created.

        Returns:
            User: The created user data.
        """
        hashed_password = pwd_context.hash(user.password)
        db_user = UserInDB(**user.dict(), password=hashed_password)
        self.db.add(db_user)
        await self.db.commit()
        await self.db.refresh(db_user)
        return User.from_orm(db_user)

    async def get_user(self, user_id: int) -> User | None:
        """
        Get a user by ID.

        Args:
            user_id (int): The ID of the user to retrieve.

        Returns:
            User | None: The retrieved user data or None if not found.
        """
        result = await self.db.execute(select(UserInDB).where(UserInDB.id == user_id))
        db_user = result.scalars().first()
        return User.from_orm(db_user) if db_user else None

# app/models/user_model.py
from sqlalchemy import Column, Integer, String, Date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class UserInDB(Base):
    __tablename__ = "users"

    id: int = Column(Integer, primary_key=True, index=True)
    username: str = Column(String(50), unique=True, index=True)
    email: str = Column(String(255), unique=True, index=True)
    first_name: str | None = Column(String(100))
    last_name: str | None = Column(String(100))
    date_of_birth: Date | None = Column(Date)
    password: str = Column(String(255))

# tests/test_entorno.py
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_user():
    response = client.post("/users/", json={"username": "testuser", "email": "test@example.com", "password": "securepassword"})
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"
    assert "id" in data

def test_get_user():
    # First, create a user to retrieve
    client.post("/users/", json={"username": "testuser", "email": "test@example.com", "password": "securepassword"})
    response = client.get("/users/1")
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"
    assert data["id"] == 1

def test_get_user_not_found():
    response = client.get("/users/999")
    assert response.status_code == 404
    assert response.json() == {"detail": "User not found"}