# setup.py
from setuptools import setup, find_packages

setup(
    name='fastapi_environment',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        'fastapi>=0.75.0',
        'uvicorn[standard]>=0.16.0',
        'sqlalchemy>=1.4.32',
        'asyncpg>=0.26.0',
        'pydantic[email]>=1.9.0',
        'redis>=4.1.0',
        'pytest>=7.1.2',
        'coverage>=6.3.2'
    ],
    extras_require={
        'dev': [
            'black>=21.12b0',
            'flake8>=4.0.1',
            'mypy>=0.931'
        ]
    },
    entry_points={
        'console_scripts': [
            'fastapi-env=app.main:main'
        ]
    }
)

# app/main.py
from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from .database import get_db
from .routers import users

app = FastAPI()

app.include_router(users.router, prefix="/users", tags=["users"])


@app.get("/")
async def read_root():
    return {"message": "Welcome to the FastAPI Environment"}


# app/routers/users.py
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from ..schemas import UserCreate, User
from ..dependencies import get_user_repo
from ..repositories.user_repository import UserRepository

router = APIRouter()


@router.post("/", response_model=User)
async def create_user(user: UserCreate, user_repo: UserRepository = Depends(get_user_repo)):
    try:
        return await user_repo.create(user)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{user_id}", response_model=User)
async def read_user(user_id: int, user_repo: UserRepository = Depends(get_user_repo)):
    try:
        return await user_repo.get_by_id(user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/{user_id}", response_model=User)
async def update_user(user_id: int, user_update: UserCreate, user_repo: UserRepository = Depends(get_user_repo)):
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
from datetime import date


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    first_name: str | None = None
    last_name: str | None = None
    date_of_birth: date | None = None


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


DATABASE_URL = (
    f"postgresql+asyncpg://{settings.database_username}:{settings.database_password}"
    f"@{settings.database_hostname}:{settings.database_port}/{settings.database_name}"
)

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
    redis_host: str = 'localhost'
    redis_port: int = 6379

    class Config:
        env_file = ".env"


settings = Settings()

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
        result = await self.session.execute(
            select(UserInDB).offset(skip).limit(limit)
        )
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

# app/services/call_processing_service.py
from .user_repository import UserRepository


class CallProcessingService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    # Placeholder for actual service logic