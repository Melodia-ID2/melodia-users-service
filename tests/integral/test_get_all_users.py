import pytest
import httpx
from tests.integral.conftest import BASE_URL

@pytest.mark.asyncio
async def test_get_all_without_admin_token_returns_401():
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        r = await client.get("/users/")
        assert r.status_code == 401
