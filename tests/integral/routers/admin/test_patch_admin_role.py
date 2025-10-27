import uuid

import pytest
from fastapi import status
from httpx import AsyncClient, Response
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.useraccount import UserAccount
from tests.integral.fixtures.factories import TestArtist, TestUser
from tests.integral.conftest import TEST_BASE_URL, auth_headers

sync_engine = create_engine(settings.DATABASE_URL.replace("+asyncpg", ""))


async def _assert_response_is_ok_and_role(response: Response, user_id: uuid.UUID, expected_role: str, session: AsyncSession) -> None:
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "id": str(user_id),
        "role": expected_role,
    }

    await session.commit()
    session.expire_all()
    user = await session.get(UserAccount, user_id)
    assert user is not None
    assert user.role == expected_role


@pytest.mark.asyncio
class TestAdminPatchRole:
    async def test_listener_to_artist(self, async_client: AsyncClient, test_listener_minimal: TestUser, session: AsyncSession) -> None:
        """Toggle role from listener to artist for an existing user."""
        response = await async_client.patch(f"{TEST_BASE_URL}/admin/{test_listener_minimal.id}/role", headers=auth_headers(uuid.uuid4(), role="admin"))
        await _assert_response_is_ok_and_role(response, test_listener_minimal.id, "artist", session)

    async def test_artist_to_listener(self, async_client: AsyncClient, test_artist_full: TestArtist, session: AsyncSession) -> None:
        """Toggle role from artist to listener for an existing user."""
        response = await async_client.patch(f"{TEST_BASE_URL}/admin/{test_artist_full.id}/role", headers=auth_headers(uuid.uuid4(), role="admin"))
        await _assert_response_is_ok_and_role(response, test_artist_full.id, "listener", session)

    async def test_nonexistent_account(self, async_client: AsyncClient) -> None:
        """Return 404 when trying to toggle role for a non-existent account."""
        missing = uuid.UUID(int=0)
        response = await async_client.patch(f"{TEST_BASE_URL}/admin/{missing}/role", headers=auth_headers(uuid.uuid4(), role="admin"))
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json() == {
            "detail": f"Cuenta de usuario con id: {missing} no encontrada",
            "instance": f"/admin/{missing}/role",
            "status": status.HTTP_404_NOT_FOUND,
            "title": "Resource Not Found",
            "type": "about:blank"
        }

    async def test_profile_inexistent_still_updates_role(self, async_client: AsyncClient, test_listener_minimal: TestUser, session: AsyncSession) -> None:
        """Update role even when user profile is missing (only account exists)."""
        await session.delete(test_listener_minimal.profile)
        await session.commit()

        response = await async_client.patch(f"{TEST_BASE_URL}/admin/{test_listener_minimal.id}/role", headers=auth_headers(uuid.uuid4(), role="admin"))
        await _assert_response_is_ok_and_role(response, test_listener_minimal.id, "artist", session)
