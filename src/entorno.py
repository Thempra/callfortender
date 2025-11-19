# app/docs/documentation.py

from fastapi import FastAPI
from pydantic import BaseModel
from typing import List

app = FastAPI(title="User Management API", version="1.0.0")

class UserBase(BaseModel):
    """
    Base model for user information.
    """
    username: str = Field(..., min_length=3, max_length=50)
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[str] = None

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

@app.post("/users/", response_model=User, tags=["Users"])
async def create_user(user: UserCreate):
    """
    Create a new user.

    Args:
        user (UserCreate): The user data to be created.

    Returns:
        User: The created user data.
    """
    # Placeholder for actual user creation logic
    return user

@app.get("/users/", response_model=List[User], tags=["Users"])
async def read_users(skip: int = 0, limit: int = 10):
    """
    Retrieve a list of users.

    Args:
        skip (int): Number of records to skip.
        limit (int): Maximum number of records to return.

    Returns:
        List[User]: A list of user data.
    """
    # Placeholder for actual user retrieval logic
    return []

@app.get("/users/{user_id}", response_model=User, tags=["Users"])
async def read_user(user_id: int):
    """
    Retrieve a user by ID.

    Args:
        user_id (int): The ID of the user to retrieve.

    Returns:
        User: The retrieved user data.
    """
    # Placeholder for actual user retrieval logic
    return {}

@app.put("/users/{user_id}", response_model=User, tags=["Users"])
async def update_user(user_id: int, user_update: UserUpdate):
    """
    Update an existing user.

    Args:
        user_id (int): The ID of the user to update.
        user_update (UserUpdate): The data to update the user with.

    Returns:
        User: The updated user data.
    """
    # Placeholder for actual user update logic
    return {}

@app.delete("/users/{user_id}", response_model=User, tags=["Users"])
async def delete_user(user_id: int):
    """
    Delete a user by ID.

    Args:
        user_id (int): The ID of the user to delete.

    Returns:
        User: The deleted user data.
    """
    # Placeholder for actual user deletion logic
    return {}