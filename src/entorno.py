# app/main.py
from fastapi import FastAPI
from .routers import users
from .database import engine, Base

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(users.router, prefix="/users", tags=["users"])


# app/routers/users.py
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from ..schemas import UserCreate, User
from ..dependencies import get_call_processing_service
from ..services.call_processing_service import CallProcessingService

router = APIRouter()

@router.post("/", response_model=User)
async def create_user(user: UserCreate, service: CallProcessingService = Depends(get_call_processing_service)):
    try:
        return await service.create(user)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{user_id}", response_model=User)
async def read_user(user_id: int, service: CallProcessingService = Depends(get_call_processing_service)):
    try:
        return await service.get_by_id(user_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.put("/{user_id}", response_model=User)
async def update_user(user_id: int, user_update: UserCreate, service: CallProcessingService = Depends(get_call_processing_service)):
    try:
        return await service.update(user_id, user_update)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{user_id}", response_model=User)
async def delete_user(user_id: int, service: CallProcessingService = Depends(get_call_processing_service)):
    try:
        return await service.delete(user_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


# app/schemas.py
from pydantic import BaseModel, EmailStr, Field
from datetime import date

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    first_name: str | None = None
    last_name: str | None = None
    date_of_birth: date | None = None

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class User(UserBase):
    id: int

    class Config:
        orm_mode = True


# app/services/call_processing_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from ..repositories.user_repository import UserRepository
from ..models.user_model import UserCreate, UserUpdate, User

class CallProcessingService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def create(self, user: UserCreate) -> User:
        return await self.user_repo.create(user)

    async def get_by_id(self, user_id: int) -> User:
        return await self.user_repo.get_by_id(user_id)

    async def update(self, user_id: int, user_update: UserUpdate) -> User:
        return await self.user_repo.update(user_id, user_update)

    async def delete(self, user_id: int) -> User:
        return await self.user_repo.delete(user_id)


# app/repositories/user_repository.py
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.user_model import UserInDB, UserCreate, UserUpdate, User
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

    async def get_by_id(self, user_id: int) -> User:
        result = await self.session.execute(select(UserInDB).where(UserInDB.id == user_id))
        db_user = result.scalar_one_or_none()
        if not db_user:
            raise ValueError(f"User with id {user_id} not found")
        return User.from_orm(db_user)

    async def update(self, user_id: int, user_update: UserUpdate) -> User:
        db_user = await self.get_by_id(user_id)
        for key, value in user_update.dict(exclude_unset=True).items():
            setattr(db_user, key, value)
        self.session.add(db_user)
        await self.session.commit()
        await self.session.refresh(db_user)
        return User.from_orm(db_user)

    async def delete(self, user_id: int) -> User:
        db_user = await self.get_by_id(user_id)
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

class UserInDB(UserInDBBase):
    hashed_password: str


# app/dependencies.py
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from .database import get_db
from .repositories.user_repository import UserRepository
from .services.call_processing_service import CallProcessingService

def get_user_repo(session: AsyncSession = Depends(get_db)) -> UserRepository:
    return UserRepository(session)

def get_call_processing_service(user_repo: UserRepository = Depends(get_user_repo)) -> CallProcessingService:
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
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.main import app

DATABASE_URL = "sqlite+aiosqlite:///./test.db"

engine = create_async_engine(DATABASE_URL, echo=True)
TestingSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

@pytest.fixture(scope="module")
async def test_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture(scope="module")
def client(test_db):
    app.dependency_overrides[get_db] = get_test_db
    yield TestClient(app)
    del app.dependency_overrides[get_db]

async def get_test_db():
    async with TestingSessionLocal() as session:
        yield session


# tests/test_users.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas import UserCreate, User
from app.main import app

@pytest.mark.asyncio
async def test_create_user(client: TestClient):
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "securepassword"
    }
    response = client.post("/users/", json=user_data)
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == user_data["username"]
    assert data["email"] == user_data["email"]

@pytest.mark.asyncio
async def test_read_user(client: TestClient):
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "securepassword"
    }
    response = client.post("/users/", json=user_data)
    assert response.status_code == 200
    data = response.json()
    user_id = data["id"]
    response = client.get(f"/users/{user_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == user_data["username"]

@pytest.mark.asyncio
async def test_update_user(client: TestClient):
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "securepassword"
    }
    response = client.post("/users/", json=user_data)
    assert response.status_code == 200
    data = response.json()
    user_id = data["id"]
    update_data = {
        "username": "updateduser",
        "email": "updated@example.com",
        "password": "newsecurepassword"
    }
    response = client.put(f"/users/{user_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == update_data["username"]

@pytest.mark.asyncio
async def test_delete_user(client: TestClient):
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "securepassword"
    }
    response = client.post("/users/", json=user_data)
    assert response.status_code == 200
    data = response.json()
    user_id = data["id"]
    response = client.delete(f"/users/{user_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == user_data["username"]