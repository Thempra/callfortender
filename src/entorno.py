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