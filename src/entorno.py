# main.py
from fastapi import FastAPI
from app.routers import users
from app.dependencies import get_db
from sqlalchemy.ext.asyncio import AsyncSession

app = FastAPI()

@app.on_event("startup")
async def startup():
    """
    Startup event to initialize the database session.
    """
    db: AsyncSession = await get_db().__anext__()
    await db.execute("SELECT 1")  # Ping the database
    await db.close()

@app.on_event("shutdown")
async def shutdown():
    """
    Shutdown event to close the database session.
    """
    pass

app.include_router(users.router, prefix="/users", tags=["users"])

# app/__init__.py
from .routers import users
from .dependencies import get_db
from .config import settings

# app/config.py
from pydantic import BaseSettings

class Settings(BaseSettings):
    """
    Configuration settings for the application.
    """
    database_hostname: str
    database_port: str
    database_password: str
    database_name: str
    database_username: str
    redis_host: str
    redis_port: int

    class Config:
        env_file = ".env"

settings = Settings()

# app/routers/users.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from ..dependencies import get_db
from ..models.user_model import UserCreate, User
from ..services.call_processing_service import CallProcessingService

router = APIRouter()

@router.post("/", response_model=User)
async def create_user(user: UserCreate, service: CallProcessingService = Depends()):
    """
    Create a new user.
    """
    try:
        return await service.create_user(user)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{user_id}", response_model=User)
async def read_user(user_id: int, service: CallProcessingService = Depends()):
    """
    Get a user by ID.
    """
    try:
        return await service.read_user(user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.put("/{user_id}", response_model=User)
async def update_user(user_id: int, user_update: UserCreate, service: CallProcessingService = Depends()):
    """
    Update a user by ID.
    """
    try:
        return await service.update_user(user_id, user_update)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/{user_id}", response_model=User)
async def delete_user(user_id: int, service: CallProcessingService = Depends()):
    """
    Delete a user by ID.
    """
    try:
        return await service.delete_user(user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

# app/dependencies.py
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_db
from .repositories.user_repository import UserRepository
from .services.call_processing_service import CallProcessingService

def get_user_repo(session: AsyncSession = Depends(get_db)) -> UserRepository:
    """
    Dependency to get the user repository.
    """
    return UserRepository(session)

def get_call_processing_service(user_repo: UserRepository = Depends(get_user_repo)) -> CallProcessingService:
    """
    Dependency to get the call processing service.
    """
    return CallProcessingService(user_repo)

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
    """
    Dependency to get the database session.
    """
    async with AsyncSessionLocal() as session:
        yield session

# app/models/user_model.py
from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from datetime import date

class UserBase(BaseModel):
    """
    Base model for user information.
    """
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[date] = None

class UserCreate(UserBase):
    """
    Model for creating a new user.
    """
    password: str = Field(..., min_length=8)

class UserUpdate(UserBase):
    """
    Model for updating an existing user.
    """

class UserInDBBase(UserBase):
    """
    Base model for user information stored in the database.
    """
    id: int

    class Config:
        orm_mode = True

class User(UserInDBBase):
    """
    Model for user information returned to the client.
    """

class UserInDB(UserInDBBase):
    """
    Model for user information stored in the database, including hashed password.
    """
    hashed_password: str

# app/services/call_processing_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from ..repositories.user_repository import UserRepository
from ..models.user_model import UserCreate, User

class CallProcessingService:
    def __init__(self, user_repo: UserRepository):
        """
        Initialize the call processing service.
        """
        self.user_repo = user_repo

    async def create_user(self, user: UserCreate) -> User:
        """
        Create a new user.
        """
        return await self.user_repo.create(user)

    async def read_user(self, user_id: int) -> User:
        """
        Get a user by ID.
        """
        return await self.user_repo.get_by_id(user_id)

    async def update_user(self, user_id: int, user_update: UserCreate) -> User:
        """
        Update an existing user.
        """
        return await self.user_repo.update(user_id, user_update)

    async def delete_user(self, user_id: int) -> User:
        """
        Delete a user by ID.
        """
        return await self.user_repo.delete(user_id)

# app/repositories/user_repository.py
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.user_model import UserInDB, UserCreate, UserUpdate, User
from .base_repository import BaseRepository

class UserRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        """
        Initialize the user repository.
        """
        super().__init__(session)

    async def create(self, user: UserCreate) -> User:
        """
        Create a new user.
        """
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
        """
        Retrieve a list of users.
        """
        result = await self.session.execute(select(UserInDB).offset(skip).limit(limit))
        return [User.from_orm(user) for user in result.scalars().all()]

    async def get_by_id(self, user_id: int) -> User:
        """
        Retrieve a user by ID.
        """
        result = await self.session.execute(select(UserInDB).where(UserInDB.id == user_id))
        db_user = result.scalar_one_or_none()
        if not db_user:
            raise ValueError(f"User with id {user_id} not found")
        return User.from_orm(db_user)

    async def update(self, user_id: int, user_update: UserUpdate) -> User:
        """
        Update an existing user.
        """
        db_user = await self.get_by_id(user_id)
        for key, value in user_update.dict(exclude_unset=True).items():
            setattr(db_user, key, value)
        self.session.add(db_user)
        await self.session.commit()
        await self.session.refresh(db_user)
        return User.from_orm(db_user)

    async def delete(self, user_id: int) -> User:
        """
        Delete a user by ID.
        """
        db_user = await self.get_by_id(user_id)
        await self.session.delete(db_user)
        await self.session.commit()
        return User.from_orm(db_user)

    def _hash_password(self, password: str) -> str:
        """
        Hash a password.
        """
        # Placeholder for actual hashing logic
        return password

# app/repositories/base_repository.py
from sqlalchemy.ext.asyncio import AsyncSession

class BaseRepository:
    def __init__(self, session: AsyncSession):
        """
        Initialize the base repository.
        """
        self.session = session