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
    pass

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
    pass

class UserInDB(UserInDBBase):
    """
    Model for user information stored in the database, including hashed password.
    """
    hashed_password: str