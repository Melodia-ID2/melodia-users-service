import asyncio
import logging
import subprocess
import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

import asyncpg
import httpx
import pytest_asyncio
from app.core.config import settings

logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
logging.getLogger("asyncpg").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
logging.getLogger("uvicorn").setLevel(logging.WARNING)
logging.getLogger("uvicorn.access").setLevel(logging.ERROR)

TEST_HOST = "0.0.0.0"
TEST_PORT = 8002
TEST_BASE_URL = f"http://{TEST_HOST}:{TEST_PORT}"
SERVER_START_TIMEOUT = 10
DB_CONNECT_TIMEOUT = 30
SERVER_POLL_INTERVAL = 0.5


async def wait_for_db() -> None:
    """Espera a que la base de datos esté lista para aceptar conexiones."""
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


async def wait_for_server() -> None:
    """Espera a que el servidor esté listo para aceptar conexiones."""
    start_time = time.monotonic()
    
    while time.monotonic() - start_time < SERVER_START_TIMEOUT:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{TEST_BASE_URL}/health")
                if response.status_code == 200:
                    return
        except (httpx.ConnectError, httpx.ReadTimeout):
            await asyncio.sleep(SERVER_POLL_INTERVAL)
    
    raise TimeoutError(
        f"El servidor no está respondiendo después de {SERVER_START_TIMEOUT} segundos"
    )


@asynccontextmanager
async def server_process() -> AsyncGenerator[None, None]:
    """Context manager para el proceso del servidor de pruebas."""
    process = await asyncio.create_subprocess_exec(
        "uvicorn",
        "app.main:app",
        "--host", TEST_HOST,
        "--port", str(TEST_PORT),
        "--log-level", "warning",
        "--no-access-log",
    )
    
    try:
        await wait_for_server()
        yield
    finally:
        if process.returncode is None:
            process.terminate()
            try:
                await asyncio.wait_for(process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()


@pytest_asyncio.fixture(scope="session")
async def server():
    """Fixture de sesión que maneja el ciclo de vida del servidor de pruebas."""
    await wait_for_db()
    
    async with server_process():
        yield


@pytest_asyncio.fixture
async def async_client(server) -> AsyncGenerator[httpx.AsyncClient, None]:
    """Proporciona un cliente HTTP asíncrono para las pruebas."""
    async with httpx.AsyncClient(base_url=TEST_BASE_URL) as client:
        yield client
