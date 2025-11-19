# setup.py

from setuptools import find_packages, setup

setup(
    name="fastapi_environment",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.75.0",
        "uvicorn[standard]>=0.16.0",
        "sqlalchemy[asyncio]>=1.4.32",
        "asyncpg>=0.26.0",
        "pydantic[email]>=1.9.1",
        "pytest>=6.2.5",
        "coverage>=6.2",
        "redis>=4.1.0",
    ],
    extras_require={
        "dev": [
            "black>=21.7b0",
            "flake8>=3.9.2",
            "mypy>=0.910",
        ]
    },
)

# .env.example

DATABASE_HOSTNAME=localhost
DATABASE_PORT=5432
DATABASE_PASSWORD=mysecretpassword
DATABASE_NAME=fastapi_db
DATABASE_USERNAME=postgres

# docker-compose.yml

version: '3.8'

services:
  db:
    image: postgres:13
    restart: always
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
    restart: always
    ports:
      - "6379:6379"

volumes:
  db_data:

# app/main.py

from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from .database import get_db
from .routers import users

app = FastAPI()

app.include_router(users.router, prefix="/users", tags=["users"])


@app.get("/")
async def read_root():
    return {"message": "Hello World"}


# app/routers/users.py

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from ..schemas import UserCreate, User
from ..crud import create_user, get_user_by_id, update_user, delete_user
from ..dependencies import get_db

router = APIRouter()


@router.post("/", response_model=User)
async def create_new_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    db_user = await create_user(db=db, user=user)
    return db_user


@router.get("/{user_id}", response_model=User)
async def read_user(user_id: int, db: AsyncSession = Depends(get_db)):
    db_user = await get_user_by_id(db=db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@router.put("/{user_id}", response_model=User)
async def update_existing_user(user_id: int, user: UserCreate, db: AsyncSession = Depends(get_db)):
    updated_user = await update_user(db=db, user_id=user_id, user=user)
    if updated_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return updated_user


@router.delete("/{user_id}", response_model=User)
async def delete_existing_user(user_id: int, db: AsyncSession = Depends(get_db)):
    deleted_user = await delete_user(db=db, user_id=user_id)
    if deleted_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return deleted_user


# app/schemas.py

from pydantic import BaseModel, EmailStr, Field
from datetime import date


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[date] = None

    class Config:
        orm_mode = True


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class User(UserBase):
    id: int


# app/crud.py

from sqlalchemy.ext.asyncio import AsyncSession
from .models import UserInDB, User
from .repositories.user_repository import UserRepository


async def create_user(db: AsyncSession, user: UserCreate) -> User:
    user_repo = UserRepository(session=db)
    db_user = await user_repo.create(user=user)
    return db_user


async def get_user_by_id(db: AsyncSession, user_id: int) -> User:
    user_repo = UserRepository(session=db)
    db_user = await user_repo.get_by_id(user_id=user_id)
    if not db_user:
        raise ValueError(f"User with id {user_id} not found")
    return db_user


async def update_user(db: AsyncSession, user_id: int, user: UserCreate) -> User:
    user_repo = UserRepository(session=db)
    updated_user = await user_repo.update(user_id=user_id, user_update=user)
    if not updated_user:
        raise ValueError(f"User with id {user_id} not found")
    return updated_user


async def delete_user(db: AsyncSession, user_id: int) -> User:
    user_repo = UserRepository(session=db)
    deleted_user = await user_repo.delete(user_id=user_id)
    if not deleted_user:
        raise ValueError(f"User with id {user_id} not found")
    return deleted_user