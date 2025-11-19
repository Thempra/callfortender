# app/main.py
from fastapi import FastAPI
from .dependencies import get_call_processing_service
from .routers import users

app = FastAPI()

app.include_router(users.router, prefix="/users", tags=["users"])

@app.get("/")
async def read_root():
    return {"message": "Welcome to the User Management API"}

# app/routers/users.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.user_model import UserCreate, UserUpdate, User
from ..dependencies import get_call_processing_service

router = APIRouter()

@router.post("/", response_model=User)
async def create_user(user: UserCreate, service=Depends(get_call_processing_service)):
    return await service.create(user)

@router.get("/{user_id}", response_model=User)
async def read_user(user_id: int, service=Depends(get_call_processing_service)):
    try:
        return await service.get_by_id(user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.put("/{user_id}", response_model=User)
async def update_user(user_id: int, user_update: UserUpdate, service=Depends(get_call_processing_service)):
    try:
        return await service.update(user_id, user_update)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/{user_id}", response_model=User)
async def delete_user(user_id: int, service=Depends(get_call_processing_service)):
    try:
        return await service.delete(user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

# app/dependencies.py
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_db
from .repositories.user_repository import UserRepository
from .services.call_processing_service import CallProcessingService

def get_user_repo(session: AsyncSession = Depends(get_db)) -> UserRepository:
    return UserRepository(session)

def get_call_processing_service(user_repo: UserRepository = Depends(get_user_repo)) -> CallProcessingService:
    return CallProcessingService(user_repo)

# app/services/call_processing_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.user_model import UserCreate, UserUpdate, User
from .user_repository import UserRepository

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
from ..models.user_model import UserCreate, UserUpdate, User

class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user: UserCreate) -> User:
        db_user = User(**user.dict())
        self.session.add(db_user)
        await self.session.commit()
        await self.session.refresh(db_user)
        return db_user

    async def get_by_id(self, user_id: int) -> User:
        user = await self.session.get(User, user_id)
        if not user:
            raise ValueError(f"User with id {user_id} not found")
        return user

    async def update(self, user_id: int, user_update: UserUpdate) -> User:
        user = await self.get_by_id(user_id)
        for key, value in user_update.dict(exclude_unset=True).items():
            setattr(user, key, value)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def delete(self, user_id: int) -> User:
        user = await self.get_by_id(user_id)
        await self.session.delete(user)
        await self.session.commit()
        return user