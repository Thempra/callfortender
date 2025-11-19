import pytest
from fastapi.testclient import TestClient
from src.app.middleware import LoggingMiddleware, AuthenticationMiddleware, add_middleware
from fastapi import FastAPI, Request, Response

# Fixtures
@pytest.fixture
def app():
    app = FastAPI()
    add_middleware(app)
    return app

@pytest.fixture
def client(app):
    return TestClient(app)

# Tests de funcionalidad básica
def test_logging_middleware_logs_request_and_response(caplog):
    async def call_next(request: Request) -> Response:
        return Response(content="OK", status_code=200)

    middleware = LoggingMiddleware(None)
    request = Request({"type": "http", "method": "GET", "path": "/test"})
    response = middleware.dispatch(request, call_next).result()

    assert response.status_code == 200
    log_messages = [record.getMessage() for record in caplog.records]
    assert f"Received GET request for URL: /test" in log_messages
    assert f"Response status code: 200" in log_messages

def test_authentication_middleware_with_valid_token():
    async def call_next(request: Request) -> Response:
        return Response(content="OK", status_code=200)

    middleware = AuthenticationMiddleware(None)
    request = Request({"type": "http", "method": "GET", "path": "/test", "headers": {"Authorization": "Bearer valid_token"}})
    response = middleware.dispatch(request, call_next).result()

    assert response.status_code == 200

def test_authentication_middleware_with_invalid_token():
    async def call_next(request: Request) -> Response:
        return Response(content="OK", status_code=200)

    middleware = AuthenticationMiddleware(None)
    request = Request({"type": "http", "method": "GET", "path": "/test", "headers": {"Authorization": "Bearer invalid_token"}})
    response = middleware.dispatch(request, call_next).result()

    assert response.status_code == 401

# Tests de edge cases
def test_logging_middleware_with_empty_path(caplog):
    async def call_next(request: Request) -> Response:
        return Response(content="OK", status_code=200)

    middleware = LoggingMiddleware(None)
    request = Request({"type": "http", "method": "GET", "path": ""})
    response = middleware.dispatch(request, call_next).result()

    assert response.status_code == 200
    log_messages = [record.getMessage() for record in caplog.records]
    assert f"Received GET request for URL: " in log_messages

def test_authentication_middleware_without_token():
    async def call_next(request: Request) -> Response:
        return Response(content="OK", status_code=200)

    middleware = AuthenticationMiddleware(None)
    request = Request({"type": "http", "method": "GET", "path": "/test"})
    response = middleware.dispatch(request, call_next).result()

    assert response.status_code == 401

# Tests de manejo de errores
def test_authentication_middleware_with_missing_authorization_header():
    async def call_next(request: Request) -> Response:
        return Response(content="OK", status_code=200)

    middleware = AuthenticationMiddleware(None)
    request = Request({"type": "http", "method": "GET", "path": "/test"})
    response = middleware.dispatch(request, call_next).result()

    assert response.status_code == 401

def test_authentication_middleware_with_invalid_token_format():
    async def call_next(request: Request) -> Response:
        return Response(content="OK", status_code=200)

    middleware = AuthenticationMiddleware(None)
    request = Request({"type": "http", "method": "GET", "path": "/test", "headers": {"Authorization": "invalid_token"}})
    response = middleware.dispatch(request, call_next).result()

    assert response.status_code == 401