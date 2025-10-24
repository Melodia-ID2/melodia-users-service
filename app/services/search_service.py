from uuid import UUID

import httpx

from app.core.config import settings
from app.schemas.user import UserSearchIndex


class SearchService:
    def __init__(self) -> None:
        self.search_service_url = settings.SEARCH_SERVICE_URL
        self.timeout = 10

    async def _make_request(self, method: str, endpoint: str, data: dict[str, str] | None = None) -> dict[str, str]:
        url = f"{self.search_service_url}{endpoint}"
        headers = {"Content-Type": "application/json"}
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.request(
                method=method,
                url=url,
                json=data,
                headers=headers
            )
            response.raise_for_status()
            return response.json()

    async def index_user(self, user_data: UserSearchIndex) -> bool:
        endpoint = "/index/users"
        try:
            await self._make_request("POST", endpoint, user_data.model_dump(exclude_none=True))
            return True
        except Exception:
            return False

    async def delete_user(self, role: str, user_id: UUID) -> bool:
        endpoint = f"/index/{role}/{str(user_id)}"
        try:
            await self._make_request("DELETE", endpoint)
            return True
        except Exception:
            return False

search_service = SearchService()
