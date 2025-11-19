# requirements.txt
fastapi[all]==0.89.1
uvicorn==0.20.0
pytest==7.2.1
coverage==6.5.0
redis==4.3.4
asyncpg==0.27.0

# docker-compose.yml
version: '3.8'

services:
  app:
    build: .
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000
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
      - db_data:/var/lib/postgresql/data

  redis:
    image: redis:6
    ports:
      - "6379:6379"

volumes:
  db_data:

# .env
DATABASE_HOSTNAME=localhost
DATABASE_PORT=5432
DATABASE_PASSWORD=mysecretpassword
DATABASE_NAME=mydatabase
DATABASE_USERNAME=myuser

# app/main.py
from fastapi import FastAPI
from app.routers import users
from app.database import engine, Base

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(users.router, prefix="/users", tags=["users"])

# app/routers/users.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas import UserCreate, UserUpdate, User
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

# app/schemas.py
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import date

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[date] = None

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class UserUpdate(UserBase):
    pass

class UserInDBBase(UserBase):
    id: int

    class Config:
        orm_mode = True

class User(UserInDBBase):
    pass

# app/repositories/user_repository.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.user import User as UserModel
from app.schemas import UserCreate, UserUpdate
from typing import Optional

class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user: UserCreate) -> UserModel:
        db_user = UserModel(
            username=user.username,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            date_of_birth=user.date_of_birth,
            password=user.password
        )
        self.session.add(db_user)
        await self.session.commit()
        await self.session.refresh(db_user)
        return db_user

    async def get_by_id(self, user_id: int) -> Optional[UserModel]:
        result = await self.session.execute(select(UserModel).where(UserModel.id == user_id))
        return result.scalars().first()

    async def update(self, user_id: int, user_update: UserUpdate) -> UserModel:
        db_user = await self.get_by_id(user_id)
        if not db_user:
            raise ValueError("User not found")
        for key, value in user_update.dict(exclude_unset=True).items():
            setattr(db_user, key, value)
        await self.session.commit()
        await self.session.refresh(db_user)
        return db_user

    async def delete(self, user_id: int) -> UserModel:
        db_user = await self.get_by_id(user_id)
        if not db_user:
            raise ValueError("User not found")
        await self.session.delete(db_user)
        await self.session.commit()
        return db_user

# app/dependencies.py
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.database import DATABASE_URL

engine = create_async_engine(DATABASE_URL, echo=True)

async_session = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session

from app.repositories.user_repository import UserRepository

def get_user_repo(session: AsyncSession = Depends(get_session)) -> UserRepository:
    return UserRepository(session)

# app/database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
import os

DATABASE_URL = f"postgresql+asyncpg://{os.getenv('DATABASE_USERNAME')}:{os.getenv('DATABASE_PASSWORD')}@{os.getenv('DATABASE_HOSTNAME')}:{os.getenv('DATABASE_PORT')}/{os.getenv('DATABASE_NAME')}"

engine = create_async_engine(DATABASE_URL, echo=True)

Base = declarative_base()

# app/models/user.py
from sqlalchemy import Column, Integer, String, Date
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    email = Column(String(255), unique=True, index=True)
    first_name = Column(String(100))
    last_name = Column(String(100))
    date_of_birth = Column(Date)
    password = Column(String(255))

# tests/test_users.py
from fastapi.testclient import TestClient
import pytest
from app.main import app

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

@pytest.mark.asyncio
async def test_create_user(client):
    response = client.post("/users/", json={"username": "testuser", "email": "test@example.com", "password": "securepassword"})
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"

@pytest.mark.asyncio
async def test_read_user(client):
    response = client.post("/users/", json={"username": "testuser", "email": "test@example.com", "password": "securepassword"})
    user_id = response.json()["id"]
    response = client.get(f"/users/{user_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"

@pytest.mark.asyncio
async def test_update_user(client):
    response = client.post("/users/", json={"username": "testuser", "email": "test@example.com", "password": "securepassword"})
    user_id = response.json()["id"]
    response = client.put(f"/users/{user_id}", json={"first_name": "John", "last_name": "Doe"})
    assert response.status_code == 200
    data = response.json()
    assert data["first_name"] == "John"
    assert data["last_name"] == "Doe"

@pytest.mark.asyncio
async def test_delete_user(client):
    response = client.post("/users/", json={"username": "testuser", "email": "test@example.com", "password": "securepassword"})
    user_id = response.json()["id"]
    response = client.delete(f"/users/{user_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"

@pytest.mark.asyncio
async def test_user_not_found(client):
    response = client.get("/users/999")
    assert response.status_code == 404
    assert response.json() == {"detail": "User not found"}