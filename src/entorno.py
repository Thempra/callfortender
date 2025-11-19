# main.py
from fastapi import FastAPI
from app.routers import users
from app.dependencies import get_db
from sqlalchemy.orm import Session

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    """
    Startup event to initialize any necessary resources.
    """
    pass

@app.on_event("shutdown")
async def shutdown_event():
    """
    Shutdown event to clean up any resources.
    """
    pass

app.include_router(users.router, prefix="/users", tags=["users"])

# app/__init__.py
from .routers import users
from .dependencies import get_db

# app/routers/users.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..schemas import UserCreate, User
from ..crud import create_user, get_users, get_user_by_id, update_user, delete_user
from ..dependencies import get_db

router = APIRouter()

@router.post("/", response_model=User)
def create_new_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    Create a new user.

    Args:
        user (UserCreate): The user data to be created.
        db (Session): The database session.

    Returns:
        User: The created user data.
    """
    db_user = create_user(db=db, user=user)
    return db_user

@router.get("/", response_model=list[User])
def read_users(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    """
    Retrieve a list of users.

    Args:
        skip (int): The number of records to skip.
        limit (int): The maximum number of records to return.
        db (Session): The database session.

    Returns:
        List[User]: A list of user data.
    """
    users = get_users(db, skip=skip, limit=limit)
    return users

@router.get("/{user_id}", response_model=User)
def read_user(user_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a single user by ID.

    Args:
        user_id (int): The ID of the user to retrieve.
        db (Session): The database session.

    Returns:
        User: The retrieved user data.
    """
    db_user = get_user_by_id(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.put("/{user_id}", response_model=User)
def update_existing_user(user_id: int, user: UserCreate, db: Session = Depends(get_db)):
    """
    Update an existing user.

    Args:
        user_id (int): The ID of the user to update.
        user (UserCreate): The updated user data.
        db (Session): The database session.

    Returns:
        User: The updated user data.
    """
    db_user = update_user(db=db, user_id=user_id, user=user)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.delete("/{user_id}", response_model=User)
def delete_existing_user(user_id: int, db: Session = Depends(get_db)):
    """
    Delete an existing user.

    Args:
        user_id (int): The ID of the user to delete.
        db (Session): The database session.

    Returns:
        User: The deleted user data.
    """
    db_user = delete_user(db=db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user