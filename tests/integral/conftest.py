import asyncio
import subprocess
import time

import asyncpg
import httpx
import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from app.core.config import settings

BASE_URL = "http://localhost:8002"
engine = create_async_engine(settings.DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def truncate_tables():
    async with engine.connect() as conn:
        try:
            await conn.execute(text("SET session_replication_role = 'replica'"))
            await conn.execute(text("TRUNCATE TABLE userprofile RESTART IDENTITY CASCADE"))
            await conn.execute(text("TRUNCATE TABLE useraccount RESTART IDENTITY CASCADE"))
            await conn.execute(text("SET session_replication_role = 'origin'"))
            await conn.commit()
        except Exception as e:
            await conn.rollback()
            print(f"Error al limpiar tablas: {e}")
            raise

async def drop_database():
    async with engine.begin() as conn:
        await conn.execute(text("DROP SCHEMA public CASCADE"))
        await conn.execute(text("CREATE SCHEMA public"))
        await conn.commit()

async def wait_for_db():
    for _ in range(30):
        try:
            conn = await asyncpg.connect(
                user=settings.DATABASE_USER,
                password=settings.DATABASE_PASSWORD,
                database=settings.DATABASE_NAME,
                host=settings.DATABASE_HOST,
                port=settings.DATABASE_PORT,
            )
            await conn.close()
            return
        except Exception:
            await asyncio.sleep(1)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def prepare_db():
    await drop_database()
    await create_tables()
    yield


@pytest_asyncio.fixture(autouse=True)
async def clean_tables_fixture():
    await truncate_tables()
    yield


@pytest.fixture(scope="session", autouse=True)
def start_server():
    """Levanta uvicorn dentro del contenedor para tests integrales."""
    asyncio.run(wait_for_db())
    proc = subprocess.Popen(["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"])

    for _ in range(20):
        try:
            r = httpx.get(f"{BASE_URL}/health")
            if r.status_code == 200:
                break
        except httpx.ConnectError:
            time.sleep(0.5)
    yield
    proc.terminate()
    proc.wait()
