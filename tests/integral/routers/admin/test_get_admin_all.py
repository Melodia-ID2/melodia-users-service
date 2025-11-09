from datetime import datetime
import uuid

import pytest
from httpx import AsyncClient, Response
from fastapi import status
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.config import settings
from app.main import app
from app.models.useraccount import UserAccount
from app.models.usercredential import UserCredential
from app.models.userprofile import UserProfile
from tests.integral.conftest import TEST_BASE_URL, auth_headers

sync_engine = create_engine(settings.DATABASE_URL.replace("+asyncpg", ""))


def insert_n_users(n: int) -> list[uuid.UUID]:
    user_ids: list[uuid.UUID] = []
    with Session(sync_engine) as session:
        for i in range(1, n + 1):
            user_id = uuid.uuid4()
            user_ids.append(user_id)
            user_account = UserAccount(id=user_id)
            user_credentials = UserCredential(user_id=user_id, email=f"email{i}@example.com", password="password")
            user_profile = UserProfile(id=user_id, username=f"username{i}", full_name=f"Full Name {i}", birthdate=datetime.fromisoformat("2000-01-01").date())
            session.add(user_account)
            session.add(user_credentials)
            session.add(user_profile)
        session.commit()
    return user_ids


def assert_n_users_in_response(response: Response, n: int, offset: int, user_ids: list[uuid.UUID]):
    assert response.status_code == 200
    data = response.json()
    assert "users" in data
    assert len(data["users"]) == n
    for i in range(n):
        user = data["users"][i]
        assert user["id"] == str(user_ids[i])
        assert user["email"] == f"email{i + 1 + offset}@example.com"
        assert user["username"] == f"username{i + 1 + offset}"
        assert user["role"] == "listener"
        assert user["status"] == "active"


def _admin_headers() -> dict[str, str]:
    return auth_headers(uuid.uuid4(), role="admin")


@pytest.mark.asyncio
class TestAdminGetAll:
    async def test_without_admin_token_returns_401(self, async_client: AsyncClient) -> None:
        """Fail with 401 when no admin token is provided."""
        response = await async_client.get(f"{TEST_BASE_URL}/admin")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json() == {
            "detail": "Token de autenticación invalido o no proporcionado",
            "instance": "/admin",
            "status": status.HTTP_401_UNAUTHORIZED,
            "title": "Authentication Error",
            "type": "about:blank",
        }

    async def test_with_admin_and_no_users_empty_list(self, async_client: AsyncClient) -> None:
        """Return an empty list when there are no users and admin is authorized."""
        response = await async_client.get(f"{TEST_BASE_URL}/admin", headers=_admin_headers())
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            "users": [],
            "total": 0,
            "page": 1,
            "pageSize": 10,
            "totalPages": 0,
        }
        app.dependency_overrides = {}

    async def test_with_admin_and_some_users(self, async_client: AsyncClient) -> None:
        """Return a list with all users when admin is authorized."""
        user_ids = insert_n_users(3)
        response = await async_client.get(f"{TEST_BASE_URL}/admin", headers=_admin_headers())
        assert response.status_code == status.HTTP_200_OK
        assert_n_users_in_response(response, 3, 0, user_ids)
        app.dependency_overrides = {}

    async def test_pagination_page_size_limits_results(self, async_client: AsyncClient) -> None:
        """Paginate results with page and page_size parameters."""
        user_ids = insert_n_users(12)
        response = await async_client.get(f"{TEST_BASE_URL}/admin?page=1&page_size=10", headers=_admin_headers())
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data["totalPages"] == 2
        assert response_data["total"] == 12
        assert_n_users_in_response(response, 10, 0, user_ids[:10])

        response = await async_client.get(f"{TEST_BASE_URL}/admin?page=2&page_size=10", headers=_admin_headers())
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert_n_users_in_response(response, 2, 10, user_ids[10:])

    async def test_with_non_admin_role_returns_401(self, async_client: AsyncClient) -> None:
        """Fail with 401 when token does not have admin role."""
        response = await async_client.get(f"{TEST_BASE_URL}/admin", headers=auth_headers(uuid.uuid4(), role="listener"))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json() == {
            "detail": "Se requiere privilegios de administrador",
            "instance": "/admin",
            "status": status.HTTP_401_UNAUTHORIZED,
            "title": "Authentication Error",
            "type": "about:blank",
        }
        app.dependency_overrides = {}
