# main.py
from fastapi import FastAPI
from app.api.routers import user_router
from app.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

app = FastAPI()

@app.on_event("startup")
async def startup():
    async with get_db() as session:
        await session.execute("SELECT 1")

@app.on_event("shutdown")
async def shutdown():
    pass

app.include_router(user_router, prefix="/users", tags=["users"])

# app/api/routers/user_router.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.user_schemas import UserCreate, UserUpdate, UserResponse
from app.services.user_service import UserService

router = APIRouter()

@router.post("/", response_model=UserResponse)
async def create_user(user: UserCreate, service: UserService = Depends(UserService)):
    return await service.create_user(user)

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, service: UserService = Depends(UserService)):
    user = await service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(user_id: int, user_update: UserUpdate, service: UserService = Depends(UserService)):
    updated_user = await service.update_user(user_id, user_update)
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")
    return updated_user

@router.delete("/{user_id}", response_model=UserResponse)
async def delete_user(user_id: int, service: UserService = Depends(UserService)):
    deleted_user = await service.delete_user(user_id)
    if not deleted_user:
        raise HTTPException(status_code=404, detail="User not found")
    return deleted_user

# app/schemas/user_schemas.py
from pydantic import BaseModel, EmailStr, Field
from datetime import date
from typing import Optional

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

class UserResponse(UserBase):
    id: int

    class Config:
        orm_mode = True

# app/services/user_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.user_repository import UserRepository
from app.schemas.user_schemas import UserCreate, UserUpdate, UserResponse
from fastapi import Depends

class UserService:
    def __init__(self, user_repo: UserRepository = Depends(UserRepository)):
        self.user_repo = user_repo

    async def create_user(self, user: UserCreate) -> UserResponse:
        return await self.user_repo.create(user)

    async def get_user(self, user_id: int) -> Optional[UserResponse]:
        return await self.user_repo.get_by_id(user_id)

    async def update_user(self, user_id: int, user_update: UserUpdate) -> Optional[UserResponse]:
        return await self.user_repo.update(user_id, user_update)

    async def delete_user(self, user_id: int) -> Optional[UserResponse]:
        return await self.user_repo.delete(user_id)

# app/repositories/user_repository.py
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user_model import UserInDB, UserCreate, UserUpdate, User
from .base_repository import BaseRepository

class UserRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def create(self, user: UserCreate) -> User:
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
        result = await self.session.execute(select(UserInDB).offset(skip).limit(limit))
        return [User.from_orm(user) for user in result.scalars().all()]

    async def get_by_id(self, user_id: int) -> Optional[User]:
        result = await self.session.execute(select(UserInDB).where(UserInDB.id == user_id))
        db_user = result.scalar_one_or_none()
        return User.from_orm(db_user) if db_user else None

    async def update(self, user_id: int, user_update: UserUpdate) -> Optional[User]:
        db_user = await self.get_by_id(user_id)
        if not db_user:
            return None
        for key, value in user_update.dict(exclude_unset=True).items():
            setattr(db_user, key, value)
        self.session.add(db_user)
        await self.session.commit()
        await self.session.refresh(db_user)
        return User.from_orm(db_user)

    async def delete(self, user_id: int) -> Optional[User]:
        db_user = await self.get_by_id(user_id)
        if not db_user:
            return None
        await self.session.delete(db_user)
        await self.session.commit()
        return User.from_orm(db_user)

    def _hash_password(self, password: str) -> str:
        # Placeholder for actual hashing logic
        return password

# app/repositories/base_repository.py
from sqlalchemy.ext.asyncio import AsyncSession

class BaseRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

# app/models/user_model.py
from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from datetime import date
from sqlalchemy import Column, Integer, String, Date
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

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

class UserInDB(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    first_name = Column(String(100))
    last_name = Column(String(100))
    date_of_birth = Column(Date)
    hashed_password = Column(String(255), nullable=False)

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

# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import engine, Base
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_db
from httpx import AsyncClient

@pytest.fixture(scope="module")
async def test_client():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield TestClient(app)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture(scope="module")
async def async_client():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture(scope="module")
async def override_get_db():
    try:
        async with AsyncSessionLocal() as session:
            yield session
    finally:
        pass

# tests/test_users.py
import pytest
from app.schemas.user_schemas import UserCreate, UserResponse
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_user(async_client: AsyncClient):
    user_data = UserCreate(username="testuser", email="test@example.com", password="password123")
    response = await async_client.post("/users/", json=user_data.dict())
    assert response.status_code == 200
    created_user = UserResponse(**response.json())
    assert created_user.username == user_data.username

@pytest.mark.asyncio
async def test_get_user(async_client: AsyncClient):
    user_data = UserCreate(username="testuser", email="test@example.com", password="password123")
    response = await async_client.post("/users/", json=user_data.dict())
    assert response.status_code == 200

    user_id = response.json()["id"]
    response = await async_client.get(f"/users/{user_id}")
    assert response.status_code == 200
    retrieved_user = UserResponse(**response.json())
    assert retrieved_user.username == user_data.username

@pytest.mark.asyncio
async def test_update_user(async_client: AsyncClient):
    user_data = UserCreate(username="testuser", email="test@example.com", password="password123")
    response = await async_client.post("/users/", json=user_data.dict())
    assert response.status_code == 200

    user_id = response.json()["id"]
    update_data = {"first_name": "John"}
    response = await async_client.put(f"/users/{user_id}", json=update_data)
    assert response.status_code == 200
    updated_user = UserResponse(**response.json())
    assert updated_user.first_name == update_data["first_name"]

@pytest.mark.asyncio
async def test_delete_user(async_client: AsyncClient):
    user_data = UserCreate(username="testuser", email="test@example.com", password="password123")
    response = await async_client.post("/users/", json=user_data.dict())
    assert response.status_code == 200

    user_id = response.json()["id"]
    response = await async_client.delete(f"/users/{user_id}")
    assert response.status_code == 200
    deleted_user = UserResponse(**response.json())
    assert deleted_user.username == user_data.username

    response = await async_client.get(f"/users/{user_id}")
    assert response.status_code == 404