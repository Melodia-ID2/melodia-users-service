from typing import AsyncGenerator

import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlmodel import SQLModel

from app.core.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def create_tables() -> None:
    """Create all tables in the database."""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def drop_database() -> None:
    """Drop all tables from the database."""
    async with engine.begin() as conn:
        await conn.execute(text("DROP SCHEMA public CASCADE"))
        await conn.execute(text("CREATE SCHEMA public"))
        await conn.commit()


async def truncate_tables() -> None:
    """Truncate all tables while keeping the schema intact."""
    async with engine.connect() as conn:
        try:
            await conn.execute(text("SET session_replication_role = 'replica'"))
            await conn.execute(text("TRUNCATE TABLE artistphoto RESTART IDENTITY CASCADE"))
            await conn.execute(text("TRUNCATE TABLE sociallink RESTART IDENTITY CASCADE"))
            await conn.execute(text("TRUNCATE TABLE userfollows RESTART IDENTITY CASCADE"))
            await conn.execute(text("TRUNCATE TABLE userprofile RESTART IDENTITY CASCADE"))
            await conn.execute(text("TRUNCATE TABLE useraccount RESTART IDENTITY CASCADE"))
            await conn.execute(text("SET session_replication_role = 'origin'"))
            await conn.commit()
        except Exception:
            await conn.rollback()
            raise


@pytest_asyncio.fixture(scope="session", autouse=True)
async def prepare_db() -> AsyncGenerator[None, None]:
    """Fixture to prepare the database before the test suite runs."""
    await drop_database()
    await create_tables()
    yield


@pytest_asyncio.fixture(autouse=True)
async def clean_tables_fixture() -> AsyncGenerator[None, None]:
    """Fixture to clean tables before each test."""
    await truncate_tables()
    yield


@pytest_asyncio.fixture
async def session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a clean AsyncSession for tests."""
    async with AsyncSessionLocal() as s:
        try:
            yield s
        finally:
            if s.in_transaction():
                await s.rollback()
