# setup.py
from setuptools import find_packages, setup

setup(
    name="fastapi_environment",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.78.0",
        "uvicorn[standard]>=0.20.0",
        "sqlalchemy>=1.4.39",
        "asyncpg>=0.26.0",
        "pydantic[email]>=1.10.5",
        "pytest>=7.1.2",
        "coverage>=6.4.1",
        "redis>=4.2.5",
        "python-dotenv>=0.20.0"
    ],
    extras_require={
        "dev": [
            "black>=22.3.0",
            "flake8>=4.0.1",
            "mypy>=0.961"
        ]
    }
)

# app/__init__.py
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def read_root():
    return {"message": "Hello World"}

# app/main.py
import uvicorn
from . import app

if __name__ == "__main__":
    uvicorn.run(app.app, host="0.0.0.0", port=8000)

# app/config/__init__.py
from pydantic import BaseSettings

class Settings(BaseSettings):
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

# app/database/__init__.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from ..config import settings

DATABASE_URL = (
    f"postgresql+asyncpg://{settings.database_username}:{settings.database_password}"
    f"@{settings.database_hostname}:{settings.database_port}/{settings.database_name}"
)

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

# app/redis_client/__init__.py
import redis.asyncio as redis
from ..config import settings

class RedisClient:
    def __init__(self, host: str, port: int):
        self.client = redis.Redis(host=host, port=port)

    async def set(self, key: str, value: str) -> None:
        """
        Set a key-value pair in Redis.

        Args:
            key (str): The key to set.
            value (str): The value to store.
        """
        await self.client.set(key, value)

    async def get(self, key: str) -> bytes:
        """
        Get the value of a key from Redis.

        Args:
            key (str): The key to retrieve.

        Returns:
            bytes: The value associated with the key.
        """
        return await self.client.get(key)

redis_client = RedisClient(host=settings.redis_host, port=settings.redis_port)