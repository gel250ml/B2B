import pytest
import pytest_asyncio
import base64
import json
from typing import AsyncGenerator
from uuid import uuid4

import httpx
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from fastapi.testclient import TestClient

from src.main import app
from src.database.dependencies import get_db, get_current_seller_id
from src.database.base import Base


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    import asyncio
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """Create a test database and return a session."""
    DATABASE_URL = "sqlite+aiosqlite:///:memory:"
    engine = create_async_engine(DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session_maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session_maker() as session:
        yield session

    await engine.dispose()


@pytest.fixture
def seller_id() -> int:
    """Return a test seller_id."""
    return 1


@pytest.fixture
def other_seller_id() -> int:
    """Return another test seller_id."""
    return 2


def create_jwt_token(seller_id: int) -> str:
    """Create a test JWT token with seller_id in claims."""
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {"seller_id": seller_id, "sub": str(seller_id)}

    header_b64 = base64.urlsafe_b64encode(
        json.dumps(header).encode()
    ).decode().rstrip("=")
    payload_b64 = base64.urlsafe_b64encode(
        json.dumps(payload).encode()
    ).decode().rstrip("=")
    signature = base64.urlsafe_b64encode(b"signature").decode().rstrip("=")

    return f"{header_b64}.{payload_b64}.{signature}"


@pytest_asyncio.fixture
async def async_client(
    test_db: AsyncSession, seller_id: int
) -> AsyncGenerator[httpx.AsyncClient, None]:
    """Create an async test client with overridden dependencies."""

    async def override_get_db():
        yield test_db

    def override_get_current_seller_id(
        authorization: str = None,
    ) -> int:
        if authorization and authorization.startswith("Bearer "):
            token = authorization.split(" ", 1)[1]
            try:
                _, payload, _ = token.split('.')
                payload += '=' * (-len(payload) % 4)
                raw = base64.urlsafe_b64decode(payload.encode())
                claims = json.loads(raw)
                return int(claims.get("seller_id", seller_id))
            except Exception:
                return seller_id
        return seller_id

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_seller_id] = override_get_current_seller_id

    async with httpx.AsyncClient(
        app=app,
        base_url="http://testserver",
    ) as client:
        yield client

    app.dependency_overrides.clear()
