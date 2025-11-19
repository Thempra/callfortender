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