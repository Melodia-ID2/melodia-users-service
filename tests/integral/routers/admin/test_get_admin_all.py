from datetime import datetime, timedelta, timezone
import uuid

import pytest
from httpx import AsyncClient, Response
from fastapi import status
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.config import settings
from app.main import app
from app.models.useraccount import UserAccount, UserRole, UserStatus
from app.models.usercredential import UserCredential
from app.models.userprofile import UserProfile
from tests.integral.conftest import TEST_BASE_URL, auth_headers

sync_engine = create_engine(settings.DATABASE_URL.replace("+asyncpg", ""))


def insert_n_users(n: int, role: UserRole = UserRole.LISTENER, start_index: int = 1) -> list[uuid.UUID]:
    user_ids: list[uuid.UUID] = []
    with Session(sync_engine) as session:
        for i in range(start_index, start_index + n):
            user_id = uuid.uuid4()
            user_ids.append(user_id)
            user_account = UserAccount(id=user_id, role=role)
            user_credentials = UserCredential(user_id=user_id, email=f"email{i}@example.com", password="password")
            user_profile = UserProfile(id=user_id, username=f"username{i}", full_name=f"Full Name {i}", birthdate=datetime.fromisoformat("2000-01-01").date())
            session.add(user_account)
            session.add(user_credentials)
            session.add(user_profile)
        session.commit()
    return user_ids


def create_user_with_details(
    username: str,
    email: str,
    role: UserRole = UserRole.LISTENER,
    status: UserStatus = UserStatus.ACTIVE,
    created_at: datetime | None = None,
) -> uuid.UUID:
    user_id = uuid.uuid4()
    with Session(sync_engine) as session:
        user_account = UserAccount(
            id=user_id,
            role=role,
            status=status,
            created_at=created_at or datetime.now(timezone.utc),
        )
        user_credentials = UserCredential(user_id=user_id, email=email, password="password")
        user_profile = UserProfile(
            id=user_id,
            username=username,
            full_name=f"Full Name {username}",
            birthdate=datetime.fromisoformat("2000-01-01").date(),
        )
        session.add(user_account)
        session.add(user_credentials)
        session.add(user_profile)
        session.commit()
    return user_id


def clear_users_table() -> None:
    with Session(sync_engine) as session:
        session.query(UserProfile).delete()
        session.query(UserCredential).delete()
        session.query(UserAccount).delete()
        session.commit()


@pytest.fixture(autouse=True)
def clean_users() -> None:
    clear_users_table()
    yield
    clear_users_table()


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

    async def test_filter_by_role(self, async_client: AsyncClient) -> None:
        """Return only users with requested role when filtering."""
        insert_n_users(2, role=UserRole.LISTENER, start_index=1)
        artist_ids = insert_n_users(1, role=UserRole.ARTIST, start_index=3)

        response = await async_client.get(f"{TEST_BASE_URL}/admin?role=artist", headers=_admin_headers())
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 1
        assert data["totalPages"] == 1
        assert data["users"] == [
            {
                "id": str(artist_ids[0]),
                "email": "email3@example.com",
                "username": "username3",
                "role": "artist",
                "status": "active",
                "profilePhoto": None,
            }
        ]
        app.dependency_overrides = {}

    async def test_sort_by_username(self, async_client: AsyncClient) -> None:
        """Sort users alphabetically by username when requested."""
        base_time = datetime(2024, 1, 1, tzinfo=timezone.utc)
        charlie_id = create_user_with_details(
            "charlie",
            "charlie@example.com",
            created_at=base_time,
        )
        alpha_id = create_user_with_details(
            "alpha",
            "alpha@example.com",
            created_at=base_time + timedelta(seconds=1),
        )
        bravo_id = create_user_with_details(
            "bravo",
            "bravo@example.com",
            created_at=base_time + timedelta(seconds=2),
        )

        response = await async_client.get(f"{TEST_BASE_URL}/admin?sort_by=username", headers=_admin_headers())
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert [user["username"] for user in data["users"]] == ["alpha", "bravo", "charlie"]
        assert [user["id"] for user in data["users"]] == [str(alpha_id), str(bravo_id), str(charlie_id)]
        app.dependency_overrides = {}

    async def test_sort_by_username_desc(self, async_client: AsyncClient) -> None:
        """Sort users by username descending when sort_order=desc."""
        base_time = datetime(2024, 1, 1, tzinfo=timezone.utc)
        alpha_id = create_user_with_details(
            "alpha",
            "alpha@example.com",
            created_at=base_time,
        )
        charlie_id = create_user_with_details(
            "charlie",
            "charlie@example.com",
            created_at=base_time + timedelta(seconds=1),
        )
        bravo_id = create_user_with_details(
            "bravo",
            "bravo@example.com",
            created_at=base_time + timedelta(seconds=2),
        )

        response = await async_client.get(f"{TEST_BASE_URL}/admin?sort_by=username&sort_order=desc", headers=_admin_headers())
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert [user["username"] for user in data["users"]] == ["charlie", "bravo", "alpha"]
        assert [user["id"] for user in data["users"]] == [str(charlie_id), str(bravo_id), str(alpha_id)]
        app.dependency_overrides = {}

    async def test_sort_by_role(self, async_client: AsyncClient) -> None:
        """Sort users by role with artists before listeners."""
        base_time = datetime(2024, 1, 1, tzinfo=timezone.utc)
        listener_first = create_user_with_details(
            "listener-1",
            "listener1@example.com",
            role=UserRole.LISTENER,
            created_at=base_time,
        )
        artist_id = create_user_with_details(
            "artist-1",
            "artist1@example.com",
            role=UserRole.ARTIST,
            created_at=base_time + timedelta(seconds=1),
        )
        listener_second = create_user_with_details(
            "listener-2",
            "listener2@example.com",
            role=UserRole.LISTENER,
            created_at=base_time + timedelta(seconds=2),
        )

        response = await async_client.get(f"{TEST_BASE_URL}/admin?sort_by=role", headers=_admin_headers())
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert [user["role"] for user in data["users"]] == ["artist", "listener", "listener"]
        assert [user["id"] for user in data["users"]] == [str(artist_id), str(listener_first), str(listener_second)]
        app.dependency_overrides = {}

    async def test_sort_by_status(self, async_client: AsyncClient) -> None:
        """Sort users by status with active before blocked."""
        base_time = datetime(2024, 1, 1, tzinfo=timezone.utc)
        blocked_id = create_user_with_details(
            "blocked-user",
            "blocked@example.com",
            status=UserStatus.BLOCKED,
            created_at=base_time,
        )
        active_id = create_user_with_details(
            "active-user",
            "active@example.com",
            status=UserStatus.ACTIVE,
            created_at=base_time + timedelta(seconds=1),
        )

        response = await async_client.get(f"{TEST_BASE_URL}/admin?sort_by=status", headers=_admin_headers())
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert [user["status"] for user in data["users"]] == ["active", "blocked"]
        assert [user["id"] for user in data["users"]] == [str(active_id), str(blocked_id)]
        app.dependency_overrides = {}
