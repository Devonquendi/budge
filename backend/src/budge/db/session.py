"""Async engine and session factory for the app's Postgres database."""

import os
from collections.abc import AsyncIterator

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession

# Needed here too: Alembic imports this module directly, outside server.py's
# own load_dotenv() call.
load_dotenv()
load_dotenv(".env.local")  # Vercel writes marketplace DB creds here


def _psycopg_url(raw: str) -> str:
    """Force SQLAlchemy onto the psycopg (v3) driver, sync or async."""
    return raw.replace("postgresql://", "postgresql+psycopg://", 1)


engine = create_async_engine(_psycopg_url(os.environ["DATABASE_URL"]))
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency yielding a request-scoped session."""
    async with async_session() as session:
        yield session
