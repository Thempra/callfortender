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
        db_call = Call(**call.dict())
        self.db.add(db_call)
        await self.db.commit()
        await self.db.refresh(db_call)
        return CallOut.from_orm(db_call)

    async def get_call(self, call_id: int) -> CallOut:
        result = await self.db.execute(select(Call).where(Call.id == call_id))
        db_call = result.scalars().first()
        if not db_call:
            raise HTTPException(status_code=404, detail="Call not found")
        return CallOut.from_orm(db_call)