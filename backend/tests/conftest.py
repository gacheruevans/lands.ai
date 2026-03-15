from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from lands_ai_backend.api.errors import register_exception_handlers
from lands_ai_backend.api.router import api_router
from lands_ai_backend.core.config import settings


@pytest.fixture
def app() -> FastAPI:
    test_app = FastAPI()
    register_exception_handlers(test_app)
    test_app.include_router(api_router, prefix=settings.api_prefix)
    return test_app


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    return TestClient(app, raise_server_exceptions=False)
