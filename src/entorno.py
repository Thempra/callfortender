# requirements.txt
fastapi==0.78.0
uvicorn[standard]==0.17.6
sqlalchemy==1.4.39
asyncpg==0.25.0
pydantic==1.10.2
pytest==7.1.2
coverage==6.4.1
redis==4.2.2

# Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# docker-compose.yml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    depends_on:
      - db
      - redis

  db:
    image: postgres:13-alpine
    environment:
      POSTGRES_USER: ${DATABASE_USERNAME}
      POSTGRES_PASSWORD: ${DATABASE_PASSWORD}
      POSTGRES_DB: ${DATABASE_NAME}
    volumes:
      - db_data:/var/lib/postgresql/data

  redis:
    image: redis:6.2-alpine

volumes:
  db_data:

# .env
DATABASE_HOSTNAME=localhost
DATABASE_PORT=5432
DATABASE_PASSWORD=mysecretpassword
DATABASE_NAME=mydatabase
DATABASE_USERNAME=myuser

# app/main.py
from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from .dependencies import get_call_processing_service
from .models.user_model import UserCreate, UserUpdate, User
from .repositories.base_repository import BaseRepository
from .services.call_processing_service import CallProcessingService

app = FastAPI()

@app.post("/users/", response_model=User)
async def create_user(user: UserCreate, service: CallProcessingService = Depends(get_call_processing_service)):
    return await service.create(user)

@app.get("/users/{user_id}", response_model=User)
async def read_user(user_id: int, service: CallProcessingService = Depends(get_call_processing_service)):
    return await service.get_by_id(user_id)

@app.put("/users/{user_id}", response_model=User)
async def update_user(user_id: int, user_update: UserUpdate, service: CallProcessingService = Depends(get_call_processing_service)):
    return await service.update(user_id, user_update)

@app.delete("/users/{user_id}", response_model=User)
async def delete_user(user_id: int, service: CallProcessingService = Depends(get_call_processing_service)):
    return await service.delete(user_id)

# app/dependencies.py
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from .database import get_db
from .repositories.user_repository import UserRepository
from .services.call_processing_service import CallProcessingService

def get_user_repo(session: AsyncSession = Depends(get_db)) -> UserRepository:
    """
    Dependency to get the user repository.

    Args:
        session (AsyncSession): The database session.

    Returns:
        UserRepository: The user repository.
    """
    return UserRepository(session)

def get_call_processing_service(user_repo: UserRepository = Depends(get_user_repo)) -> CallProcessingService:
    """
    Dependency to get the call processing service.

    Args:
        user_repo (UserRepository): The user repository.

    Returns:
        CallProcessingService: The call processing service.
    """
    return CallProcessingService(user_repo)

# tests/test_entorno.py
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_read_main():
    response = client.get("/")
    assert response.status_code == 404
    assert response.json() == {"detail": "Not Found"}

def test_create_user():
    user_data = {
        "name": "John Doe",
        "email": "john.doe@example.com"
    }
    response = client.post("/users/", json=user_data)
    assert response.status_code == 200
    assert response.json()["name"] == user_data["name"]
    assert response.json()["email"] == user_data["email"]

def test_read_user():
    user_id = 1
    response = client.get(f"/users/{user_id}")
    assert response.status_code == 200
    assert response.json()["id"] == user_id

def test_update_user():
    user_id = 1
    update_data = {
        "name": "Jane Doe",
        "email": "jane.doe@example.com"
    }
    response = client.put(f"/users/{user_id}", json=update_data)
    assert response.status_code == 200
    assert response.json()["name"] == update_data["name"]
    assert response.json()["email"] == update_data["email"]

def test_delete_user():
    user_id = 1
    response = client.delete(f"/users/{user_id}")
    assert response.status_code == 200
    assert response.json()["id"] == user_id