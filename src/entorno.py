# app/main.py
from fastapi import FastAPI
from app.api.routers import user_router
from app.database import engine, Base

Base.metadata.create_all(bind=engine)

app = FastAPI(title="User Management API", version="1.0.0")

app.include_router(user_router.router, prefix="/users", tags=["users"])


# app/api/routers/user_router.py
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_model import UserCreate, UserUpdate, User
from app.services.user_service import UserService
from app.dependencies import get_db

router = APIRouter()

@router.post("/", response_model=User)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    user_service = UserService(db)
    created_user = await user_service.create_user(user)
    return created_user

@router.get("/{user_id}", response_model=User)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    user_service = UserService(db)
    user = await user_service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.put("/{user_id}", response_model=User)
async def update_user(user_id: int, user_update: UserUpdate, db: AsyncSession = Depends(get_db)):
    user_service = UserService(db)
    updated_user = await user_service.update_user(user_id, user_update)
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")
    return updated_user

@router.delete("/{user_id}", response_model=User)
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db)):
    user_service = UserService(db)
    deleted_user = await user_service.delete_user(user_id)
    if not deleted_user:
        raise HTTPException(status_code=404, detail="User not found")
    return deleted_user


# app/services/user_service.py
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_model import UserCreate, UserUpdate, UserInDB, User
from app.repositories.user_repository import UserRepository

class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)

    async def create_user(self, user_create: UserCreate) -> User:
        hashed_password = self._hash_password(user_create.password)
        user_in_db = UserInDB(
            username=user_create.username,
            email=user_create.email,
            first_name=user_create.first_name,
            last_name=user_create.last_name,
            date_of_birth=user_create.date_of_birth,
            hashed_password=hashed_password
        )
        created_user = await self.user_repo.create(user_in_db)
        return User.from_orm(created_user)

    async def get_user(self, user_id: int) -> User:
        db_user = await self.user_repo.get_by_id(user_id)
        if not db_user:
            return None
        return User.from_orm(db_user)

    async def update_user(self, user_id: int, user_update: UserUpdate) -> User:
        db_user = await self.user_repo.update(user_id, user_update)
        if not db_user:
            return None
        return User.from_orm(db_user)

    async def delete_user(self, user_id: int) -> User:
        db_user = await self.user_repo.delete(user_id)
        if not db_user:
            return None
        return User.from_orm(db_user)

    def _hash_password(self, password: str) -> str:
        # Placeholder for actual hashing logic
        return password


# app/repositories/user_repository.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.user_model import UserInDB, User

class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user_in_db: UserInDB) -> UserInDB:
        self.session.add(user_in_db)
        await self.session.commit()
        await self.session.refresh(user_in_db)
        return user_in_db

    async def get_by_id(self, user_id: int) -> UserInDB:
        result = await self.session.execute(select(UserInDB).where(UserInDB.id == user_id))
        db_user = result.scalar_one_or_none()
        return db_user

    async def update(self, user_id: int, user_update: UserUpdate) -> UserInDB:
        db_user = await self.get_by_id(user_id)
        if not db_user:
            return None
        for key, value in user_update.dict(exclude_unset=True).items():
            setattr(db_user, key, value)
        self.session.add(db_user)
        await self.session.commit()
        await self.session.refresh(db_user)
        return db_user

    async def delete(self, user_id: int) -> UserInDB:
        db_user = await self.get_by_id(user_id)
        if not db_user:
            return None
        await self.session.delete(db_user)
        await self.session.commit()
        return db_user


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


# app/dependencies.py
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from .database import get_db
from .repositories.user_repository import UserRepository
from .services.user_service import UserService

def get_user_repo(session: AsyncSession = Depends(get_db)) -> UserRepository:
    return UserRepository(session)

def get_call_processing_service(user_repo: UserRepository = Depends(get_user_repo)) -> UserService:
    return UserService(user_repo)