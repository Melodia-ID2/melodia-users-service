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
    NOTIFICATION_BITS_MASK,
)
from tests.integral.conftest import TEST_BASE_URL, TestUser, auth_headers
from tests.integral.routers.preferences.helpers import (
    set_user_preferences,
    get_user_preferences,
    assert_bit_is_set,
    assert_bit_is_not_set,
    expected_error_response,
)


@pytest.mark.asyncio
class TestPutNotificationPreferences:
    """Tests for the PUT /preferences/notifications endpoint."""

    async def test_put_notifications_enable_all(self, async_client: AsyncClient, test_listener_full: TestUser, session: AsyncSession) -> None:
        """Successfully enable all notification preferences."""
        await set_user_preferences(session, test_listener_full.id, BIT_KEEP_HISTORY)

        request_body = {
            "newReleases": True,
            "followedActivity": True,
            "socialActivity": True,
        }

        response = await async_client.put(
            f"{TEST_BASE_URL}/preferences/notifications",
            headers=auth_headers(test_listener_full.id, role="listener"),
            json=request_body,
        )

        assert response.status_code == status.HTTP_200_OK, \
            f"Expected status code 200, got {response.status_code}. Response: {response.text}"
        assert response.json() == {
            "newReleases": True,
            "followedActivity": True,
            "socialActivity": True,
        }

        preferences = await get_user_preferences(session, test_listener_full.id)
        assert_bit_is_set(preferences, BIT_NOTIFICATIONS_NEW_RELEASES)
        assert_bit_is_set(preferences, BIT_NOTIFICATIONS_FOLLOWED_ACTIVITY)
        assert_bit_is_set(preferences, BIT_NOTIFICATIONS_SOCIAL_ACTIVITY)
        assert_bit_is_set(preferences, BIT_KEEP_HISTORY)

    async def test_put_notifications_disable_all(self, async_client: AsyncClient, test_listener_full: TestUser, session: AsyncSession) -> None:
        """Successfully disable all notification preferences."""
        await set_user_preferences(session, test_listener_full.id, DEFAULT_PREFERENCES)

        request_body = {
            "newReleases": False,
            "followedActivity": False,
            "socialActivity": False,
        }

        response = await async_client.put(
            f"{TEST_BASE_URL}/preferences/notifications",
            headers=auth_headers(test_listener_full.id, role="listener"),
            json=request_body,
        )

        assert response.status_code == status.HTTP_200_OK, \
            f"Expected status code 200, got {response.status_code}. Response: {response.text}"
        assert response.json() == {
            "newReleases": False,
            "followedActivity": False,
            "socialActivity": False,
        }

        preferences = await get_user_preferences(session, test_listener_full.id)
        assert_bit_is_not_set(preferences, BIT_NOTIFICATIONS_NEW_RELEASES)
        assert_bit_is_not_set(preferences, BIT_NOTIFICATIONS_FOLLOWED_ACTIVITY)
        assert_bit_is_not_set(preferences, BIT_NOTIFICATIONS_SOCIAL_ACTIVITY)
        assert_bit_is_set(preferences, BIT_KEEP_HISTORY)

    async def test_put_notifications_partial_update(self, async_client: AsyncClient, test_listener_full: TestUser, session: AsyncSession) -> None:
        """Successfully update some notification preferences while keeping others."""
        await set_user_preferences(session, test_listener_full.id, DEFAULT_PREFERENCES)

        request_body = {
            "newReleases": True,
            "followedActivity": False,
            "socialActivity": True,
        }

        response = await async_client.put(
            f"{TEST_BASE_URL}/preferences/notifications",
            headers=auth_headers(test_listener_full.id, role="listener"),
            json=request_body,
        )

        assert response.status_code == status.HTTP_200_OK, \
            f"Expected status code 200, got {response.status_code}. Response: {response.text}"
        assert response.json() == {
            "newReleases": True,
            "followedActivity": False,
            "socialActivity": True,
        }

        preferences = await get_user_preferences(session, test_listener_full.id)
        assert_bit_is_set(preferences, BIT_NOTIFICATIONS_NEW_RELEASES)
        assert_bit_is_not_set(preferences, BIT_NOTIFICATIONS_FOLLOWED_ACTIVITY)
        assert_bit_is_set(preferences, BIT_NOTIFICATIONS_SOCIAL_ACTIVITY)

    async def test_put_notifications_preserves_history_flag_when_enabled(self, async_client: AsyncClient, test_listener_full: TestUser, session: AsyncSession) -> None:
        """History flag remains enabled after updating notification preferences."""
        await set_user_preferences(session, test_listener_full.id, BIT_KEEP_HISTORY | BIT_NOTIFICATIONS_NEW_RELEASES)

        request_body = {
            "newReleases": False,
            "followedActivity": True,
            "socialActivity": False,
        }

        response = await async_client.put(
            f"{TEST_BASE_URL}/preferences/notifications",
            headers=auth_headers(test_listener_full.id, role="listener"),
            json=request_body,
        )

        assert response.status_code == status.HTTP_200_OK
        preferences = await get_user_preferences(session, test_listener_full.id)
        assert_bit_is_set(preferences, BIT_KEEP_HISTORY)

    async def test_put_notifications_preserves_history_flag_when_disabled(self, async_client: AsyncClient, test_listener_full: TestUser, session: AsyncSession) -> None:
        """History flag remains disabled after updating notification preferences."""
        await set_user_preferences(session, test_listener_full.id, BIT_NOTIFICATIONS_NEW_RELEASES)

        request_body = {
            "newReleases": False,
            "followedActivity": True,
            "socialActivity": True,
        }

        response = await async_client.put(
            f"{TEST_BASE_URL}/preferences/notifications",
            headers=auth_headers(test_listener_full.id, role="listener"),
            json=request_body,
        )

        assert response.status_code == status.HTTP_200_OK
        preferences = await get_user_preferences(session, test_listener_full.id)
        assert_bit_is_not_set(preferences, BIT_KEEP_HISTORY)

    async def test_put_notifications_toggle_single_preference(self, async_client: AsyncClient, test_listener_full: TestUser, session: AsyncSession) -> None:
        """Successfully toggle a single notification preference."""
        initial_prefs = BIT_KEEP_HISTORY | BIT_NOTIFICATIONS_NEW_RELEASES | BIT_NOTIFICATIONS_SOCIAL_ACTIVITY
        await set_user_preferences(session, test_listener_full.id, initial_prefs)

        request_body = {
            "newReleases": False,
            "followedActivity": False,
            "socialActivity": True,
        }

        response = await async_client.put(
            f"{TEST_BASE_URL}/preferences/notifications",
            headers=auth_headers(test_listener_full.id, role="listener"),
            json=request_body,
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            "newReleases": False,
            "followedActivity": False,
            "socialActivity": True,
        }

        preferences = await get_user_preferences(session, test_listener_full.id)
        assert_bit_is_not_set(preferences, BIT_NOTIFICATIONS_NEW_RELEASES)
        assert_bit_is_not_set(preferences, BIT_NOTIFICATIONS_FOLLOWED_ACTIVITY)
        assert_bit_is_set(preferences, BIT_NOTIFICATIONS_SOCIAL_ACTIVITY)
        assert_bit_is_set(preferences, BIT_KEEP_HISTORY)

    async def test_put_notifications_idempotent(self, async_client: AsyncClient, test_listener_full: TestUser, session: AsyncSession) -> None:
        """Updating with same values is idempotent."""
        await set_user_preferences(session, test_listener_full.id, DEFAULT_PREFERENCES)

        request_body = {
            "newReleases": True,
            "followedActivity": True,
            "socialActivity": True,
        }

        response1 = await async_client.put(
            f"{TEST_BASE_URL}/preferences/notifications",
            headers=auth_headers(test_listener_full.id, role="listener"),
            json=request_body,
        )
        assert response1.status_code == status.HTTP_200_OK

        response2 = await async_client.put(
            f"{TEST_BASE_URL}/preferences/notifications",
            headers=auth_headers(test_listener_full.id, role="listener"),
            json=request_body,
        )
        assert response2.status_code == status.HTTP_200_OK
        assert response1.json() == response2.json()

        preferences = await get_user_preferences(session, test_listener_full.id)
        assert preferences == DEFAULT_PREFERENCES

    async def test_put_notifications_for_artist(self, async_client: AsyncClient, test_artist_full: TestUser, session: AsyncSession) -> None:
        """Artists can also update their notification preferences."""
        await set_user_preferences(session, test_artist_full.id, BIT_KEEP_HISTORY)

        request_body = {
            "newReleases": True,
            "followedActivity": False,
            "socialActivity": True,
        }

        response = await async_client.put(
            f"{TEST_BASE_URL}/preferences/notifications",
            headers=auth_headers(test_artist_full.id, role="artist"),
            json=request_body,
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == request_body

    async def test_put_notifications_with_all_false_clears_notification_bits(self, async_client: AsyncClient, test_listener_full: TestUser, session: AsyncSession) -> None:
        """Setting all notifications to false clears only notification bits."""
        await set_user_preferences(session, test_listener_full.id, DEFAULT_PREFERENCES)

        request_body = {
            "newReleases": False,
            "followedActivity": False,
            "socialActivity": False,
        }

        response = await async_client.put(
            f"{TEST_BASE_URL}/preferences/notifications",
            headers=auth_headers(test_listener_full.id, role="listener"),
            json=request_body,
        )

        assert response.status_code == status.HTTP_200_OK
        preferences = await get_user_preferences(session, test_listener_full.id)
        assert preferences & NOTIFICATION_BITS_MASK == 0
        assert_bit_is_set(preferences, BIT_KEEP_HISTORY)

    async def test_put_notifications_unauthenticated(self, async_client: AsyncClient) -> None:
        """Attempting to update notification preferences without authentication fails."""
        request_body = {
            "newReleases": True,
            "followedActivity": True,
            "socialActivity": True,
        }

        response = await async_client.put(
            f"{TEST_BASE_URL}/preferences/notifications",
            json=request_body,
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json() == expected_error_response(
            401,
            "Token de autenticación invalido o no proporcionado",
            "/preferences/notifications"
        )

    async def test_put_notifications_nonexistent_user(self, async_client: AsyncClient) -> None:
        """Attempting to update notification preferences for a nonexistent user fails."""
        nonexistent_user_id = uuid.uuid4()
        request_body = {
            "newReleases": True,
            "followedActivity": False,
            "socialActivity": True,
        }

        response = await async_client.put(
            f"{TEST_BASE_URL}/preferences/notifications",
            headers=auth_headers(nonexistent_user_id, role="listener"),
            json=request_body,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json() == expected_error_response(
            404,
            "Usuario no encontrado",
            "/preferences/notifications"
        )

    async def test_put_notifications_invalid_payload_missing_fields(self, async_client: AsyncClient, test_listener_full: TestUser) -> None:
        """Sending incomplete payload fails validation."""
        request_body = {
            "newReleases": True,
        }

        response = await async_client.put(
            f"{TEST_BASE_URL}/preferences/notifications",
            headers=auth_headers(test_listener_full.id, role="listener"),
            json=request_body,
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_put_notifications_invalid_payload_wrong_types(self, async_client: AsyncClient, test_listener_full: TestUser) -> None:
        """Sending invalid data types fails validation."""
        request_body: dict[str, str | int] = {
            "newReleases": "string",
            "followedActivity": "string",
            "socialActivity": 3,
        }

        response = await async_client.put(
            f"{TEST_BASE_URL}/preferences/notifications",
            headers=auth_headers(test_listener_full.id, role="listener"),
            json=request_body,
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_put_notifications_empty_payload(self, async_client: AsyncClient, test_listener_full: TestUser) -> None:
        """Sending empty payload fails validation."""
        response = await async_client.put(
            f"{TEST_BASE_URL}/preferences/notifications",
            headers=auth_headers(test_listener_full.id, role="listener"),
            json={},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
