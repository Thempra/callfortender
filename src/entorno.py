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

from fastapi import FastAPI  # Limitar tamaño