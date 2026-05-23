from collections.abc import AsyncGenerator
from unittest.mock import MagicMock

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from src.core.config import settings
from src.services.inventory_db_service import SessionLocal, init_inventory_db

settings.SERVICE_TOKEN = "test-token"
settings.GEMINI_API_KEY = "test-key"
settings.CHROMA_DB_DIR = "/tmp/test_chroma"
settings.INVENTORY_DATABASE_URL = "sqlite:///./test_inventory.db"
settings.INVENTORY_MODEL_PATH = "/tmp/test_models.joblib"


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    db = SessionLocal()
    try:
        init_inventory_db(db)
    finally:
        db.close()
    yield
    import os as _os

    for f in ["./test_inventory.db", "./test_inventory.db-wal", "./test_inventory.db-shm"]:
        if _os.path.exists(f):
            _os.remove(f)


@pytest.fixture
def app() -> FastAPI:
    from src.main import app

    app.dependency_overrides.clear()
    app.state.http_client = MagicMock()
    app.state.recommendation_service = MagicMock()
    app.state.recommendation_service.provider = "gemini"
    app.state.search_service = MagicMock()
    app.state.forecaster = MagicMock()
    app.state.transcriber = MagicMock()
    return app


@pytest_asyncio.fixture
async def client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.fixture
def auth_headers() -> dict[str, str]:
    return {"X-Service-Token": "test-token"}
