import uuid
import pytest
from httpx import AsyncClient
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.notification_flags import (
    BIT_KEEP_HISTORY,
    BIT_NOTIFICATIONS_NEW_RELEASES,
    BIT_NOTIFICATIONS_FOLLOWED_ACTIVITY,
    BIT_NOTIFICATIONS_SOCIAL_ACTIVITY,
    DEFAULT_PREFERENCES,
)
from tests.integral.conftest import TEST_BASE_URL, TestUser, auth_headers
from tests.integral.routers.preferences.helpers import (
    set_user_preferences,
    get_user_preferences,
    assert_bit_is_not_set,
    expected_error_response,
)


@pytest.mark.asyncio
class TestGetNotificationPreferences:
    """Tests for the GET /preferences/notifications endpoint."""

    async def test_get_notifications_with_all_enabled(self, async_client: AsyncClient, test_listener_full: TestUser, session: AsyncSession) -> None:
        """Successfully retrieve notification preferences when all are enabled."""
        all_notifications_enabled = (
            BIT_NOTIFICATIONS_NEW_RELEASES
            | BIT_NOTIFICATIONS_FOLLOWED_ACTIVITY
            | BIT_NOTIFICATIONS_SOCIAL_ACTIVITY
        )
        await set_user_preferences(session, test_listener_full.id, all_notifications_enabled | BIT_KEEP_HISTORY)

        response = await async_client.get(
            f"{TEST_BASE_URL}/preferences/notifications",
            headers=auth_headers(test_listener_full.id, role="listener"),
        )

        assert response.status_code == status.HTTP_200_OK, \
            f"Expected status code 200, got {response.status_code}. Response: {response.text}"
        assert response.json() == {
            "newReleases": True,
            "followedActivity": True,
            "socialActivity": True,
        }

    async def test_get_notifications_with_all_disabled(self, async_client: AsyncClient, test_listener_full: TestUser, session: AsyncSession) -> None:
        """Successfully retrieve notification preferences when all are disabled."""
        await set_user_preferences(session, test_listener_full.id, BIT_KEEP_HISTORY)

        response = await async_client.get(
            f"{TEST_BASE_URL}/preferences/notifications",
            headers=auth_headers(test_listener_full.id, role="listener"),
        )

        assert response.status_code == status.HTTP_200_OK, \
            f"Expected status code 200, got {response.status_code}. Response: {response.text}"
        assert response.json() == {
            "newReleases": False,
            "followedActivity": False,
            "socialActivity": False,
        }

    async def test_get_notifications_with_default_preferences(self, async_client: AsyncClient, test_listener_full: TestUser, session: AsyncSession) -> None:
        """Successfully retrieve notification preferences with default values."""
        await set_user_preferences(session, test_listener_full.id, DEFAULT_PREFERENCES)

        response = await async_client.get(
            f"{TEST_BASE_URL}/preferences/notifications",
            headers=auth_headers(test_listener_full.id, role="listener"),
        )

        assert response.status_code == status.HTTP_200_OK, \
            f"Expected status code 200, got {response.status_code}. Response: {response.text}"
        assert response.json() == {
            "newReleases": True,
            "followedActivity": True,
            "socialActivity": True,
        }

    async def test_get_notifications_with_partial_preferences(self, async_client: AsyncClient, test_listener_full: TestUser, session: AsyncSession) -> None:
        """Successfully retrieve notification preferences when some are enabled."""
        partial_preferences = BIT_NOTIFICATIONS_NEW_RELEASES | BIT_NOTIFICATIONS_SOCIAL_ACTIVITY
        await set_user_preferences(session, test_listener_full.id, partial_preferences | BIT_KEEP_HISTORY)

        response = await async_client.get(
            f"{TEST_BASE_URL}/preferences/notifications",
            headers=auth_headers(test_listener_full.id, role="listener"),
        )

        assert response.status_code == status.HTTP_200_OK, \
            f"Expected status code 200, got {response.status_code}. Response: {response.text}"
        assert response.json() == {
            "newReleases": True,
            "followedActivity": False,
            "socialActivity": True,
        }

    async def test_get_notifications_preserves_history_flag(self, async_client: AsyncClient, test_listener_full: TestUser, session: AsyncSession) -> None:
        """Verify that history flag is independent of notification preferences."""
        await set_user_preferences(session, test_listener_full.id, BIT_NOTIFICATIONS_NEW_RELEASES)

        response = await async_client.get(
            f"{TEST_BASE_URL}/preferences/notifications",
            headers=auth_headers(test_listener_full.id, role="listener"),
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            "newReleases": True,
            "followedActivity": False,
            "socialActivity": False,
        }

        preferences = await get_user_preferences(session, test_listener_full.id)
        assert_bit_is_not_set(preferences, BIT_KEEP_HISTORY)

    async def test_get_notifications_for_artist(self, async_client: AsyncClient, test_artist_full: TestUser, session: AsyncSession) -> None:
        """Artists can also retrieve their notification preferences."""
        await set_user_preferences(session, test_artist_full.id, DEFAULT_PREFERENCES)

        response = await async_client.get(
            f"{TEST_BASE_URL}/preferences/notifications",
            headers=auth_headers(test_artist_full.id, role="artist"),
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            "newReleases": True,
            "followedActivity": True,
            "socialActivity": True,
        }

    async def test_get_notifications_unauthenticated(self, async_client: AsyncClient) -> None:
        """Attempting to retrieve notification preferences without authentication fails."""
        response = await async_client.get(f"{TEST_BASE_URL}/preferences/notifications")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json() == expected_error_response(
            401,
            "Token de autenticación invalido o no proporcionado",
            "/preferences/notifications"
        )

    async def test_get_notifications_nonexistent_user(self, async_client: AsyncClient) -> None:
        """Attempting to retrieve notification preferences for a nonexistent user fails."""
        nonexistent_user_id = uuid.uuid4()
        response = await async_client.get(
            f"{TEST_BASE_URL}/preferences/notifications",
            headers=auth_headers(nonexistent_user_id, role="listener"),
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json() == expected_error_response(
            404,
            "Usuario no encontrado",
            "/preferences/notifications"
        )
