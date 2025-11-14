from typing import Dict, Any
from uuid import UUID

import httpx

from app.core.config import settings
from app.schemas.user import UserSearchIndex


class SearchService:
    def __init__(self) -> None:
        self.orchestrator_url = settings.API_GATEWAY_URL.rstrip("/") + "/orchestrator/enqueue"
        self.search_service_url = settings.API_GATEWAY_URL.rstrip("/") + "/search"
        self.timeout = 5

    def _enqueue_search_task(self, method: str, endpoint: str, payload: dict[str, str] | None = None) -> Dict[str, Any]:
        try:
            full_endpoint = f"{self.search_service_url}{endpoint}"
            task_payload = {
                "endpoint": full_endpoint,
                "method": method,
                "headers": {
                    "content-type": "application/json",
                },
                "max_attempts": 3,
                "timeout": 30,
            }
            
            if payload:
                task_payload["payload"] = payload

            with httpx.Client(timeout=httpx.Timeout(self.timeout, connect=2.0)) as client:
                resp = client.post(self.orchestrator_url, json=task_payload)
                return {
                    "status_code": resp.status_code,
                    "text": resp.text[:500],
                }
        except Exception as e:
            return {"error": str(e)}

    def index_user(self, user_data: UserSearchIndex) -> bool:
        endpoint = "/index/users"
        try:
            result = self._enqueue_search_task("POST", endpoint, user_data.model_dump(exclude_none=True))
            return result.get("status_code", 0) < 400
        except Exception:
            return False

    def delete_user(self, role: str, user_id: UUID) -> bool:
        endpoint = f"/index/{role}/{str(user_id)}"
        try:
            result = self._enqueue_search_task("DELETE", endpoint)
            return result.get("status_code", 0) < 400
        except Exception:
            return False

search_service = SearchService()
