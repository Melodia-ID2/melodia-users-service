import asyncio
import logging
import time
from typing import AsyncGenerator, Optional

import asyncpg
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.core.config import settings
from app.main import app

logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
logging.getLogger("asyncpg").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)

TEST_BASE_URL = "http://test"
DB_CONNECT_TIMEOUT = 30


async def wait_for_db() -> None:
    """Wait for the database to be ready to accept connections."""
    start_time = time.monotonic()
    last_error: Optional[Exception] = None
    
    while time.monotonic() - start_time < DB_CONNECT_TIMEOUT:
        try:
            conn = await asyncio.wait_for(
                asyncpg.connect(
                    user=settings.DATABASE_USER,
                    password=settings.DATABASE_PASSWORD,
                    database=settings.DATABASE_NAME,
                    host=settings.DATABASE_HOST,
                    port=settings.DATABASE_PORT,
                ),
                timeout=1.0
            )
            await conn.close()
            return
        except (OSError, ConnectionRefusedError, asyncio.TimeoutError) as e:
            last_error = e
            await asyncio.sleep(0.5)
    
    raise TimeoutError(
        f"No se pudo conectar a la base de datos después de {DB_CONNECT_TIMEOUT} segundos: {last_error}"
    )


@pytest_asyncio.fixture(scope="session")
async def server():
    """Session-scoped fixture that ensures DB is ready."""
    await wait_for_db()
    yield


@pytest_asyncio.fixture
async def async_client(server) -> AsyncGenerator[AsyncClient, None]:
    """Provide an asynchronous HTTP client for tests using ASGI transport.
    
    This runs the FastAPI app directly in the same process, so coverage
    is automatically captured without needing a subprocess.
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url=TEST_BASE_URL) as client:
        yield client
