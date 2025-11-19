# main.py
from fastapi import FastAPI
from app.routers import users
from app.dependencies import get_db
from sqlalchemy.ext.asyncio import AsyncSession

app = FastAPI()

@app.on_event("startup")
async def startup():
    """
    Startup event to initialize the application.
    """
    pass

@app.on_event("shutdown")
async def shutdown():
    """
    Shutdown event to clean up resources.
    """
    pass

app.include_router(users.router, prefix="/users", tags=["users"])

# app/__init__.py
from .routers import users
from .dependencies import get_db

# app/routers/users.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from ..schemas import UserCreate, User
from ..services.user_service import UserService

router = APIRouter()

@router.post("/", response_model=User)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    Create a new user.

    Args:
        user (UserCreate): The user data to be created.
        db (AsyncSession): The database session.

    Returns:
        User: The created user data.
    """
    service = UserService(db)
    return await service.create_user(user)

@router.get("/{user_id}", response_model=User)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    """
    Get a user by ID.

    Args:
        user_id (int): The ID of the user to retrieve.
        db (AsyncSession): The database session.

    Returns:
        User: The retrieved user data.
    """
    service = UserService(db)
    user = await service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# app/schemas.py
from pydantic import BaseModel, EmailStr, Field
from datetime import date

class UserBase(BaseModel):
    """
    Base model for user information.
    """
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    first_name: str | None = None
    last_name: str | None = None
    date_of_birth: date | None = None

class UserCreate(UserBase):
    """
    Model for creating a new user.
    """
    password: str = Field(..., min_length=8)

class User(UserBase):
    """
    Model for user information returned to the client.
    """
    id: int

    class Config:
        orm_mode = True

# app/services/user_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.user_model import UserInDB, UserCreate
from ..schemas import User
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserService:
    def __init__(self, db: AsyncSession):
        """
        Initialize the user service.

        Args:
            db (AsyncSession): The database session.
        """
        self.db = db

    async def create_user(self, user: UserCreate) -> User:
        """
        Create a new user.

        Args:
            user (UserCreate): The user data to be created.

        Returns:
            User: The created user data.
        """
        hashed_password = pwd_context.hash(user.password)
        db_user = UserInDB(**user.dict(), hashed_password=hashed_password)
        self.db.add(db_user)
        await self.db.commit()
        await self.db.refresh(db_user)
        return User.from_orm(db_user)

    async def get_user(self, user_id: int) -> User | None:
        """
        Get a user by ID.

        Args:
            user_id (int): The ID of the user to retrieve.

        Returns:
            User | None: The retrieved user data or None if not found.
        """
        result = await self.db.execute(select(UserInDB).where(UserInDB.id == user_id))
        return result.scalar_one_or_none()

# app/models/user_model.py
from sqlalchemy import Column, Integer, String, Date
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class UserInDB(Base):
    """
    Model for user information stored in the database.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    first_name = Column(String(100))
    last_name = Column(String(100))
    date_of_birth = Column(Date)
    hashed_password = Column(String(255), nullable=False)

# app/dependencies.py
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from .database import get_db
from .repositories.user_repository import UserRepository

def get_user_repo(session: AsyncSession = Depends(get_db)) -> UserRepository:
    """
    Dependency to get the user repository.

    Args:
        session (AsyncSession): The database session.

    Returns:
        UserRepository: The user repository.
    """
    return UserRepository(session)

# app/repositories/user_repository.py
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.user_model import UserInDB
from ..schemas import UserCreate, User

class UserRepository:
    def __init__(self, session: AsyncSession):
        """
        Initialize the user repository.

        Args:
            session (AsyncSession): The database session.
        """
        self.session = session

    async def create_user(self, user: UserCreate) -> User:
        """
        Create a new user.

        Args:
            user (UserCreate): The user data to be created.

        Returns:
            User: The created user data.
        """
        db_user = UserInDB(**user.dict())
        self.session.add(db_user)
        await self.session.commit()
        await self.session.refresh(db_user)
        return User.from_orm(db_user)

    async def get_user(self, user_id: int) -> User | None:
        """
        Get a user by ID.

        Args:
            user_id (int): The ID of the user to retrieve.

        Returns:
            User | None: The retrieved user data or None if not found.
        """
        result = await self.session.execute(select(UserInDB).where(UserInDB.id == user_id))
        return result.scalar_one_or_none()

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

    Yields:
        AsyncSession: The database session.
    """
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
DATABASE_HOSTNAME=localhost
DATABASE_PORT=5432
DATABASE_PASSWORD=mysecretpassword
DATABASE_NAME=mydatabase
DATABASE_USERNAME=myuser

# requirements.txt
fastapi[all]
asyncpg
passlib
bcrypt
pytest
coverage
redis