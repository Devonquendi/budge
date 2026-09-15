"""A whole app on SQLite, so the request routes can be exercised for real.

The environment is set before anything under `budge` is imported: db/session.py
builds its engine at module level, which is also why one missing variable takes
the whole app down rather than one route. These are assignments rather than
defaults on purpose. A developer's own .env is loaded by mise before pytest
starts, and a test that passes or fails depending on it is worthless.
"""

import os
from collections.abc import AsyncIterator

import pytest
from cryptography.fernet import Fernet

INVITE_CODE = "test-invite"

os.environ["DATABASE_URL"] = "sqlite+aiosqlite://"
os.environ["DATABASE_URL_UNPOOLED"] = "sqlite://"
os.environ["AUTH_SECRET"] = "test-secret"
os.environ["CREDENTIALS_ENCRYPTION_KEY"] = Fernet.generate_key().decode()
os.environ["SIGNUP_INVITE_CODE"] = INVITE_CODE
# The demo routes switch themselves off in production and nowhere else.
os.environ.pop("VERCEL_ENV", None)

from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from budge.db.session import get_session
from budge.server import app

Sessions = async_sessionmaker[AsyncSession]


@pytest.fixture
async def db() -> AsyncIterator[Sessions]:
    """An empty database per test, and the factory the app will read it through."""
    # One connection shared by every session: an in-memory database belongs to
    # its connection, so a pool would hand out empty ones.
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as connection:
        await connection.run_sync(SQLModel.metadata.create_all)

    yield async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    await engine.dispose()


@pytest.fixture
async def client(db: Sessions) -> AsyncIterator[AsyncClient]:
    """A signed-out client against that database."""

    async def session_override() -> AsyncIterator[AsyncSession]:
        async with db() as session:
            yield session

    app.dependency_overrides[get_session] = session_override
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client

    app.dependency_overrides.clear()
