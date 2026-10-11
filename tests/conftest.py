import os

os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest-at-least-32-bytes")

import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import event
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestSessionLocal = async_sessionmaker(bind=test_engine, expire_on_commit=False)

PASSWORD = "supersecret123"


@event.listens_for(test_engine.sync_engine, "connect")
def _enable_sqlite_foreign_keys(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


async def _override_get_db():
    async with TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


app.dependency_overrides[get_db] = _override_get_db


@pytest_asyncio.fixture(autouse=True)
async def setup_database():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


async def _make_authenticated_client(email: str) -> AsyncClient:
    ac = AsyncClient(transport=ASGITransport(app=app), base_url="http://test")
    await ac.post("/auth/register", json={"email": email, "password": PASSWORD})
    response = await ac.post(
        "/auth/login", data={"username": email, "password": PASSWORD}
    )
    ac.headers["Authorization"] = f"Bearer {response.json()['access_token']}"
    return ac


@pytest_asyncio.fixture
async def auth_client():
    ac = await _make_authenticated_client("owner@example.com")
    yield ac
    await ac.aclose()


@pytest_asyncio.fixture
async def other_client():
    ac = await _make_authenticated_client("other@example.com")
    yield ac
    await ac.aclose()