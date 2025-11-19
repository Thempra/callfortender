# app/main.py
from fastapi import FastAPI
from .routers import call_router, user_router

app = FastAPI()

app.include_router(call_router.router, prefix="/calls", tags=["Calls"])
app.include_router(user_router.router, prefix="/users", tags=["Users"])


# app/routers/call_router.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..schemas.call_schema import CallCreate, CallUpdate, CallResponse
from ..services.call_service import CallService
from ..dependencies import get_call_repo

router = APIRouter()

@router.post("/", response_model=CallResponse)
async def create_call(call: CallCreate, call_service: CallService = Depends(get_call_repo)):
    return await call_service.create_call(call)

@router.get("/{call_id}", response_model=CallResponse)
async def read_call(call_id: int, call_service: CallService = Depends(get_call_repo)):
    call = await call_service.get_call_by_id(call_id)
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    return call

@router.put("/{call_id}", response_model=CallResponse)
async def update_call(call_id: int, call_update: CallUpdate, call_service: CallService = Depends(get_call_repo)):
    updated_call = await call_service.update_call(call_id, call_update)
    if not updated_call:
        raise HTTPException(status_code=404, detail="Call not found")
    return updated_call

@router.delete("/{call_id}", response_model=CallResponse)
async def delete_call(call_id: int, call_service: CallService = Depends(get_call_repo)):
    deleted_call = await call_service.delete_call(call_id)
    if not deleted_call:
        raise HTTPException(status_code=404, detail="Call not found")
    return deleted_call


# app/routers/user_router.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..schemas.user_schema import UserCreate, UserUpdate, UserResponse
from ..services.user_service import UserService
from ..dependencies import get_user_repo

router = APIRouter()

@router.post("/", response_model=UserResponse)
async def create_user(user: UserCreate, user_service: UserService = Depends(get_user_repo)):
    return await user_service.create_user(user)

@router.get("/{user_id}", response_model=UserResponse)
async def read_user(user_id: int, user_service: UserService = Depends(get_user_repo)):
    user = await user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(user_id: int, user_update: UserUpdate, user_service: UserService = Depends(get_user_repo)):
    updated_user = await user_service.update_user(user_id, user_update)
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")
    return updated_user

@router.delete("/{user_id}", response_model=UserResponse)
async def delete_user(user_id: int, user_service: UserService = Depends(get_user_repo)):
    deleted_user = await user_service.delete_user(user_id)
    if not deleted_user:
        raise HTTPException(status_code=404, detail="User not found")
    return deleted_user


# app/schemas/call_schema.py
from pydantic import BaseModel
from datetime import datetime

class CallBase(BaseModel):
    caller_id: int
    receiver_id: int
    call_time: datetime

class CallCreate(CallBase):
    pass

class CallUpdate(CallBase):
    pass

class CallResponse(CallBase):
    id: int

    class Config:
        orm_mode = True


# app/schemas/user_schema.py
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

class UserResponse(UserBase):
    id: int

    class Config:
        orm_mode = True


# app/services/call_service.py
from sqlalchemy.ext.asyncio import AsyncSession

from ..repositories.call_repository import CallRepository
from ..schemas.call_schema import CallCreate, CallUpdate, CallResponse

class CallService:
    def __init__(self, call_repo: CallRepository):
        self.call_repo = call_repo

    async def create_call(self, call: CallCreate) -> CallResponse:
        return await self.call_repo.create(call)

    async def get_call_by_id(self, call_id: int) -> CallResponse | None:
        return await self.call_repo.get_by_id(call_id)

    async def update_call(self, call_id: int, call_update: CallUpdate) -> CallResponse | None:
        return await self.call_repo.update(call_id, call_update)

    async def delete_call(self, call_id: int) -> CallResponse | None:
        return await self.call_repo.delete(call_id)


# app/services/user_service.py
from sqlalchemy.ext.asyncio import AsyncSession

from ..repositories.user_repository import UserRepository
from ..schemas.user_schema import UserCreate, UserUpdate, UserResponse

class UserService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def create_user(self, user: UserCreate) -> UserResponse:
        return await self.user_repo.create(user)

    async def get_user_by_id(self, user_id: int) -> UserResponse | None:
        return await self.user_repo.get_by_id(user_id)

    async def update_user(self, user_id: int, user_update: UserUpdate) -> UserResponse | None:
        return await self.user_repo.update(user_id, user_update)

    async def delete_user(self, user_id: int) -> UserResponse | None:
        return await self.user_repo.delete(user_id)


# app/repositories/call_repository.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from ..models.call_model import CallInDB, CallCreate, CallUpdate, Call
from .base_repository import BaseRepository

class CallRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def create(self, call: CallCreate) -> Call:
        db_call = CallInDB(
            caller_id=call.caller_id,
            receiver_id=call.receiver_id,
            call_time=call.call_time
        )
        self.session.add(db_call)
        await self.session.commit()
        await self.session.refresh(db_call)
        return Call.from_orm(db_call)

    async def get_by_id(self, call_id: int) -> Call | None:
        result = await self.session.execute(select(CallInDB).where(CallInDB.id == call_id))
        db_call = result.scalar_one_or_none()
        if not db_call:
            return None
        return Call.from_orm(db_call)

    async def update(self, call_id: int, call_update: CallUpdate) -> Call | None:
        db_call = await self.get_by_id(call_id)
        if not db_call:
            return None
        for key, value in call_update.dict(exclude_unset=True).items():
            setattr(db_call, key, value)
        self.session.add(db_call)
        await self.session.commit()
        await self.session.refresh(db_call)
        return Call.from_orm(db_call)

    async def delete(self, call_id: int) -> Call | None:
        db_call = await self.get_by_id(call_id)
        if not db_call:
            return None
        await self.session.delete(db_call)
        await self.session.commit()
        return Call.from_orm(db_call)


# app/models/call_model.py
from sqlalchemy import Column, Integer, DateTime, ForeignKey

from .base_model import Base

class CallInDB(Base):
    __tablename__ = "calls"

    id = Column(Integer, primary_key=True, index=True)
    caller_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    call_time = Column(DateTime, nullable=False)

class CallCreate:
    caller_id: int
    receiver_id: int
    call_time: DateTime

class CallUpdate:
    caller_id: int | None = None
    receiver_id: int | None = None
    call_time: DateTime | None = None

class Call(CallInDB):
    class Config:
        orm_mode = True


# app/dependencies.py
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from .repositories.call_repository import CallRepository
from .repositories.user_repository import UserRepository
from .database import get_db

def get_call_repo(session: AsyncSession = Depends(get_db)) -> CallRepository:
    return CallRepository(session)

def get_user_repo(session: AsyncSession = Depends(get_db)) -> UserRepository:
    return UserRepository(session)


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


# app/models/base_model.py
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()