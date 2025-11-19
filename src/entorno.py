# app/infrastructure/__init__.py

from .database import get_db, AsyncSessionLocal, engine
from .redis_client import RedisClient
from .settings import Settings

__all__ = [
    "get_db",
    "AsyncSessionLocal",
    "engine",
    "RedisClient",
    "Settings"
]

# app/infrastructure/database.py

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from ..config import settings

DATABASE_URL = (
    f"postgresql+asyncpg://{settings.database_username}:"
    f"{settings.database_password}@{settings.database_hostname}:"
    f"{settings.database_port}/{settings.database_name}"
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

# app/infrastructure/redis_client.py

import redis.asyncio as redis
from ..config import settings


class RedisClient:
    """
    A client for interacting with a Redis server.

    Attributes:
        _client (redis.Redis): The underlying Redis client.
    """

    def __init__(self):
        self._client = redis.from_url(
            f"redis://{settings.redis_hostname}:{settings.redis_port}"
        )

    async def set(self, key: str, value: str, ex: int = None) -> bool:
        """
        Set the string value of a key.

        Args:
            key (str): The key to set.
            value (str): The value to set for the key.
            ex (int, optional): Expiration time in seconds. Defaults to None.

        Returns:
            bool: True if the operation was successful, False otherwise.
        """
        return await self._client.set(key, value, ex=ex)

    async def get(self, key: str) -> str:
        """
        Get the string value of a key.

        Args:
            key (str): The key to retrieve.

        Returns:
            str: The value of the key, or None if the key does not exist.
        """
        return await self._client.get(key)

    async def delete(self, *keys: str) -> int:
        """
        Delete one or more keys.

        Args:
            *keys (str): The keys to delete.

        Returns:
            int: The number of keys that were removed.
        """
        return await self._client.delete(*keys)

# app/infrastructure/settings.py

from pydantic import BaseSettings


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Attributes:
        database_hostname (str): The hostname of the PostgreSQL database.
        database_port (str): The port number of the PostgreSQL database.
        database_password (str): The password for the PostgreSQL database.
        database_name (str): The name of the PostgreSQL database.
        database_username (str): The username for the PostgreSQL database.
        redis_hostname (str): The hostname of the Redis server.
        redis_port (int): The port number of the Redis server.
    """

    database_hostname: str
    database_port: str
    database_password: str
    database_name: str
    database_username: str
    redis_hostname: str = "localhost"
    redis_port: int = 6379

    class Config:
        env_file = ".env"

settings = Settings()