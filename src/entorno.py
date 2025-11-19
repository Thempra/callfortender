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