# app/middleware.py

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log request and response details.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Log the request path and method before passing it to the next middleware or route handler.
        Log the response status code after receiving it from the route handler.

        Args:
            request (Request): The incoming request object.
            call_next: The next middleware or route handler in the stack.

        Returns:
            Response: The outgoing response object.
        """
        start_time = time.time()
        logger.info(f"Received {request.method} request for URL: {request.url.path}")
        response = await call_next(request)
        process_time = (time.time() - start_time) * 1000
        logger.info(
            f"Completed {request.method} request to {request.url.path}: "
            f"{response.status_code} in {process_time:.2f}ms"
        )
        return response

class AuthenticationMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle authentication for incoming requests.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Check if the request is authenticated before passing it to the next middleware or route handler.

        Args:
            request (Request): The incoming request object.
            call_next: The next middleware or route handler in the stack.

        Returns:
            Response: The outgoing response object.
        """
        # Example authentication check
        auth_header = request.headers.get("Authorization")
        if not auth_header or not self.is_valid_token(auth_header):
            return Response(content="Unauthorized", status_code=401)
        response = await call_next(request)
        return response

    def is_valid_token(self, token: str) -> bool:
        """
        Validate the provided authentication token.

        Args:
            token (str): The authentication token to validate.

        Returns:
            bool: True if the token is valid, False otherwise.
        """
        # Example token validation logic
        return token == "valid-token"

def add_middleware(app: FastAPI) -> None:
    """
    Add middleware to the FastAPI application.

    Args:
        app (FastAPI): The FastAPI application instance.
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(AuthenticationMiddleware)

# __init__.py

from fastapi import FastAPI
from .middleware import add_middleware
from .routers import user_router  # Assuming you have a router defined in routers/user.py

app = FastAPI()

add_middleware(app)
app.include_router(user_router, prefix="/users", tags=["users"])

# routers/user.py

from fastapi import APIRouter, HTTPException
from ..models.user_model import UserCreate, User
from ..services.call_processing_service import CallProcessingService
from ..dependencies import get_call_processing_service
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

router = APIRouter()

@router.post("/", response_model=User)
async def create_user(
    user_create: UserCreate,
    call_processing_service: CallProcessingService = Depends(get_call_processing_service),
) -> User:
    """
    Create a new user.

    Args:
        user_create (UserCreate): The data for the new user.
        call_processing_service (CallProcessingService): The service to handle user creation.

    Returns:
        User: The created user.
    """
    try:
        return await call_processing_service.create_user(user_create)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[User])
async def get_users(
    skip: int = 0,
    limit: int = 10,
    call_processing_service: CallProcessingService = Depends(get_call_processing_service),
) -> List[User]:
    """
    Retrieve a list of users.

    Args:
        skip (int): The number of users to skip.
        limit (int): The maximum number of users to return.
        call_processing_service (CallProcessingService): The service to handle user retrieval.

    Returns:
        List[User]: A list of users.
    """
    try:
        return await call_processing_service.get_users(skip, limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{user_id}", response_model=User)
async def get_user(
    user_id: int,
    call_processing_service: CallProcessingService = Depends(get_call_processing_service),
) -> User:
    """
    Retrieve a single user by ID.

    Args:
        user_id (int): The ID of the user to retrieve.
        call_processing_service (CallProcessingService): The service to handle user retrieval.

    Returns:
        User: The retrieved user.
    """
    try:
        return await call_processing_service.get_user(user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{user_id}", response_model=User)
async def update_user(
    user_id: int,
    user_update: UserCreate,
    call_processing_service: CallProcessingService = Depends(get_call_processing_service),
) -> User:
    """
    Update an existing user.

    Args:
        user_id (int): The ID of the user to update.
        user_update (UserCreate): The data for updating the user.
        call_processing_service (CallProcessingService): The service to handle user updates.

    Returns:
        User: The updated user.
    """
    try:
        return await call_processing_service.update_user(user_id, user_update)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{user_id}", response_model=User)
async def delete_user(
    user_id: int,
    call_processing_service: CallProcessingService = Depends(get_call_processing_service),
) -> User:
    """
    Delete a user by ID.

    Args:
        user_id (int): The ID of the user to delete.
        call_processing_service (CallProcessingService): The service to handle user deletion.

    Returns:
        User: The deleted user.
    """
    try:
        return await call_processing_service.delete_user(user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# services/call_processing_service.py

from sqlalchemy.ext.asyncio import AsyncSession
from ..models.user_model import UserCreate, UserInDB, User
from ..repositories.user_repository import UserRepository
from typing import List
from fastapi import Depends
from ..dependencies import get_user_repo

class CallProcessingService:
    """
    Service to handle user operations.
    """

    def __init__(self, user_repo: UserRepository = Depends(get_user_repo)):
        """
        Initialize the service with a user repository.

        Args:
            user_repo (UserRepository): The repository for user data access.
        """
        self.user_repo = user_repo

    async def create_user(self, user_create: UserCreate) -> User:
        """
        Create a new user.

        Args:
            user_create (UserCreate): The data for the new user.

        Returns:
            User: The created user.
        """
        return await self.user_repo.create(user_create)

    async def get_users(self, skip: int = 0, limit: int = 10) -> List[User]:
        """
        Retrieve a list of users.

        Args:
            skip (int): The number of users to skip.
            limit (int): The maximum number of users to return.

        Returns:
            List[User]: A list of users.
        """
        return await self.user_repo.get_all(skip, limit)

    async def get_user(self, user_id: int) -> User:
        """
        Retrieve a single user by ID.

        Args:
            user_id (int): The ID of the user to retrieve.

        Returns:
            User: The retrieved user.
        """
        return await self.user_repo.get_by_id(user_id)

    async def update_user(self, user_id: int, user_update: UserCreate) -> User:
        """
        Update an existing user.

        Args:
            user_id (int): The ID of the user to update.
            user_update (UserCreate): The data for updating the user.

        Returns:
            User: The updated user.
        """
        return await self.user_repo.update(user_id, user_update)

    async def delete_user(self, user_id: int) -> User:
        """
        Delete a user by ID.

        Args:
            user_id (int): The ID of the user to delete.

        Returns:
            User: The deleted user.
        """
        return await self.user_repo.delete(user_id)