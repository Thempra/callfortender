# app/main.py
from fastapi import FastAPI
from app.api.routers import call_router, user_router
from app.database import engine, Base

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Call Management API")

app.include_router(call_router.router, prefix="/calls", tags=["Calls"])
app.include_router(user_router.router, prefix="/users", tags=["Users"])


# app/api/routers/call_router.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.call_schema import CallCreate, CallOut
from app.services.call_service import CallService
from app.dependencies import get_db

router = APIRouter()

@router.post("/", response_model=CallOut)
async def create_call(call: CallCreate, db: AsyncSession = Depends(get_db)):
    call_service = CallService(db)
    created_call = await call_service.create_call(call)
    return created_call

@router.get("/{call_id}", response_model=CallOut)
async def get_call(call_id: int, db: AsyncSession = Depends(get_db)):
    call_service = CallService(db)
    call = await call_service.get_call(call_id)
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    return call


# app/api/routers/user_router.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.user_schema import UserCreate, UserOut
from app.services.user_service import UserService
from app.dependencies import get_db

router = APIRouter()

@router.post("/", response_model=UserOut)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    user_service = UserService(db)
    created_user = await user_service.create_user(user)
    return created_user

@router.get("/{user_id}", response_model=UserOut)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    user_service = UserService(db)
    user = await user_service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# app/schemas/call_schema.py
from pydantic import BaseModel
from datetime import datetime

class CallCreate(BaseModel):
    caller_id: int
    receiver_id: int
    call_time: datetime

class CallOut(CallCreate):
    id: int

    class Config:
        orm_mode = True


# app/schemas/user_schema.py
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date

class UserBase(BaseModel):
    username: str
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[date] = None

class UserCreate(UserBase):
    password: str

class UserOut(UserBase):
    id: int

    class Config:
        orm_mode = True


# app/services/call_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.call_model import Call
from app.schemas.call_schema import CallCreate, CallOut

class CallService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_call(self, call: CallCreate) -> CallOut:
        new_call = Call(**call.dict())
        self.db.add(new_call)
        await self.db.commit()
        await self.db.refresh(new_call)
        return CallOut.from_orm(new_call)

    async def get_call(self, call_id: int) -> CallOut:
        result = await self.db.execute(select(Call).where(Call.id == call_id))
        call = result.scalar_one_or_none()
        if not call:
            raise ValueError(f"Call with id {call_id} not found")
        return CallOut.from_orm(call)


# app/services/user_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.user_model import User, UserInDB
from app.schemas.user_schema import UserCreate, UserOut
from app.repositories.user_repository import UserRepository

class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)

    async def create_user(self, user: UserCreate) -> UserOut:
        new_user = await self.user_repo.create(user)
        return UserOut.from_orm(new_user)

    async def get_user(self, user_id: int) -> UserOut:
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError(f"User with id {user_id} not found")
        return UserOut.from_orm(user)


# app/models/call_model.py
from sqlalchemy import Column, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from app.database import Base

class Call(Base):
    __tablename__ = "calls"

    id = Column(Integer, primary_key=True, index=True)
    caller_id = Column(Integer, ForeignKey("users.id"))
    receiver_id = Column(Integer, ForeignKey("users.id"))
    call_time = Column(DateTime)

    caller = relationship("User", foreign_keys=[caller_id])
    receiver = relationship("User", foreign_keys=[receiver_id])


# app/models/user_model.py
from sqlalchemy import Column, Integer, String, Date

from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    first_name = Column(String)
    last_name = Column(String)
    date_of_birth = Column(Date)


class UserInDB(User):
    hashed_password = Column(String)


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


# .env
database_hostname=localhost
database_port=5432
database_password=mysecretpassword
database_name=mydatabase
database_username=myuser


# app/__init__.py
# Source package initialization