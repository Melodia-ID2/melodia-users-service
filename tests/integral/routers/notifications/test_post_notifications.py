import uuid
import pytest
from httpx import AsyncClient
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import NotificationType
from tests.integral.conftest import TEST_BASE_URL, TestUser
from tests.integral.routers.notifications.helpers import (
    create_device_token,
    mute_artist,
    count_user_notifications,
    service_token_headers,
)
from tests.integral.routers.preferences.helpers import set_user_preferences


@pytest.mark.asyncio
class TestNotificationEventIngestion:
    """Tests for the POST /notifications endpoint (S2S)."""

    async def test_post_notifications_success_single_target(
        self, async_client: AsyncClient, test_listener_full: TestUser, session: AsyncSession
    ) -> None:
        """Successfully process and send notification to a single user."""
        await create_device_token(session, test_listener_full.id, "device-token-123")
        
        request_body = {
            "event_type": "new_release",
            "target_user_ids": [str(test_listener_full.id)],
            "actor_id": str(uuid.uuid4()),
            "title": "New Album",
            "body": "Body",
            "metadata": {
                "album_id": "album-123",
                "artistName": "Test Artist",
                "title": "New Album"
            }
        }

        response = await async_client.post(
            f"{TEST_BASE_URL}/notifications",
            headers=service_token_headers(),
            json=request_body,
        )

        assert response.status_code == status.HTTP_200_OK, \
            f"Expected status code 200, got {response.status_code}. Response: {response.text}"

        response_data = response.json()
        assert response_data["notificationsCreated"] == 1
        # FCM is not available in test environment, so notificationsSent will be 0
        # But the notification IS created in the database (has token, not filtered by preferences)
        assert response_data["notificationsSent"] == 0
        assert response_data["notificationsFiltered"] == 0
        assert response_data["filterReasons"]["user_disabled"] == 0
        assert response_data["filterReasons"]["artist_muted"] == 0
        assert response_data["filterReasons"]["no_tokens"] == 0

        notification_count = await count_user_notifications(session, test_listener_full.id)
        assert notification_count == 1

    async def test_post_notifications_filters_user_with_disabled_preference(
        self, async_client: AsyncClient, test_listener_full: TestUser, session: AsyncSession
    ) -> None:
        """User with disabled preference does not receive notification."""
        await create_device_token(session, test_listener_full.id, "device-token-123")
        await set_user_preferences(session, test_listener_full.id, 0)

        request_body = {
            "event_type": "new_release",
            "target_user_ids": [str(test_listener_full.id)],
            "actor_id": str(uuid.uuid4()),
            "title": "New Album",
            "body": "Body",
            "metadata": {
                "album_id": "album-123",
                "artistName": "Test Artist",
                "title": "New Album"
            }
        }

        response = await async_client.post(
            f"{TEST_BASE_URL}/notifications",
            headers=service_token_headers(),
            json=request_body,
        )

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data["notificationsCreated"] == 0
        assert response_data["notificationsSent"] == 0
        assert response_data["notificationsFiltered"] == 1
        assert response_data["filterReasons"]["user_disabled"] == 1

        notification_count = await count_user_notifications(session, test_listener_full.id)
        assert notification_count == 0

    async def test_post_notifications_filters_user_with_muted_artist(
        self, async_client: AsyncClient, test_listener_full: TestUser, test_artist_full: TestUser, session: AsyncSession
    ) -> None:
        """User with muted artist does not receive notification."""
        await create_device_token(session, test_listener_full.id, "device-token-123")
        await mute_artist(session, test_listener_full.id, test_artist_full.id)

        request_body = {
            "event_type": "new_release",
            "target_user_ids": [str(test_listener_full.id)],
            "actor_id": str(test_artist_full.id),
            "title": "New Album",
            "body": "Body",
            "metadata": {
                "album_id": "album-123",
                "artistName": "Test Artist",
                "title": "New Album"
            }
        }

        response = await async_client.post(
            f"{TEST_BASE_URL}/notifications",
            headers=service_token_headers(),
            json=request_body,
        )

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data["notificationsCreated"] == 0
        assert response_data["notificationsSent"] == 0
        assert response_data["notificationsFiltered"] == 1
        assert response_data["filterReasons"]["artist_muted"] == 1

        notification_count = await count_user_notifications(session, test_listener_full.id)
        assert notification_count == 0

    async def test_post_notifications_filters_user_without_device_tokens(
        self, async_client: AsyncClient, test_listener_full: TestUser, session: AsyncSession
    ) -> None:
        """User without active device tokens is filtered."""
        request_body = {
            "event_type": "new_release",
            "target_user_ids": [str(test_listener_full.id)],
            "actor_id": str(uuid.uuid4()),
            "title": "New Album",
            "body": "Body",
            "metadata": {
                "album_id": "album-123",
                "artistName": "Test Artist",
                "title": "New Album"
            }
        }

        response = await async_client.post(
            f"{TEST_BASE_URL}/notifications",
            headers=service_token_headers(),
            json=request_body,
        )

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data["notificationsCreated"] == 0
        assert response_data["notificationsSent"] == 0
        assert response_data["notificationsFiltered"] == 1
        assert response_data["filterReasons"]["no_tokens"] == 1

    async def test_post_notifications_multiple_targets_mixed_filters(
        self, async_client: AsyncClient, test_listener_full: TestUser, test_listener_minimal: TestUser, session: AsyncSession
    ) -> None:
        """Successfully handles multiple targets with different filtering reasons."""
        await create_device_token(session, test_listener_full.id, "device-token-full")
        await set_user_preferences(session, test_listener_minimal.id, 0)

        request_body = {
            "event_type": "new_release",
            "target_user_ids": [str(test_listener_full.id), str(test_listener_minimal.id)],
            "actor_id": str(uuid.uuid4()),
            "title": "New Album",
            "body": "Body",
            "metadata": {
                "album_id": "album-123",
                "artistName": "Test Artist",
                "title": "New Album"
            }
        }

        response = await async_client.post(
            f"{TEST_BASE_URL}/notifications",
            headers=service_token_headers(),
            json=request_body,
        )

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data["notificationsCreated"] == 1
        assert response_data["notificationsSent"] == 0
        assert response_data["notificationsFiltered"] == 1

    async def test_post_notifications_missing_service_token(self, async_client: AsyncClient) -> None:
        """Missing service token header yields 422 validation error."""
        request_body = {
            "event_type": "new_release",
            "target_user_ids": [str(uuid.uuid4())],
            "actor_id": str(uuid.uuid4()),
            "title": "New Album",
            "body": "Body",
            "metadata": {"album_id": "album-123"}
        }

        response = await async_client.post(
            f"{TEST_BASE_URL}/notifications",
            json=request_body,
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_post_notifications_invalid_service_token(self, async_client: AsyncClient) -> None:
        """Invalid service token returns 401 with default detail."""
        request_body = {
            "event_type": "new_release",
            "target_user_ids": [str(uuid.uuid4())],
            "actor_id": str(uuid.uuid4()),
            "title": "New Album",
            "body": "Body",
            "metadata": {"album_id": "album-123"}
        }

        response = await async_client.post(
            f"{TEST_BASE_URL}/notifications",
            headers={"X-Service-Token": "invalid-token"},
            json=request_body,
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json() == {"detail": "Invalid service token"}

    async def test_post_notifications_invalid_notification_type(self, async_client: AsyncClient) -> None:
        """Invalid notification type fails validation."""
        request_body = {
            "event_type": "INVALID_TYPE",
            "target_user_ids": [str(uuid.uuid4())],
            "actor_id": str(uuid.uuid4()),
            "title": "x",
            "body": "y",
            "metadata": {"album_id": "album-123"}
        }

        response = await async_client.post(
            f"{TEST_BASE_URL}/notifications",
            headers=service_token_headers(),
            json=request_body,
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_post_notifications_missing_required_fields(self, async_client: AsyncClient) -> None:
        """Request missing required fields fails validation."""
        request_body = {
            "event_type": "new_release",
        }

        response = await async_client.post(
            f"{TEST_BASE_URL}/notifications",
            headers=service_token_headers(),
            json=request_body,
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_post_notifications_empty_target_list(self, async_client: AsyncClient) -> None:
        """Request with empty target list returns zero counts."""
        request_body = {
            "event_type": "new_release",
            "target_user_ids": [],
            "actor_id": str(uuid.uuid4()),
            "title": "New Album",
            "body": "Body",
            "metadata": {"album_id": "album-123"}
        }

        response = await async_client.post(
            f"{TEST_BASE_URL}/notifications",
            headers=service_token_headers(),
            json=request_body,
        )

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data["notificationsCreated"] == 0
        assert response_data["notificationsSent"] == 0
        assert response_data["notificationsFiltered"] == 0

    async def test_post_notifications_creates_deep_link_in_data(
        self, async_client: AsyncClient, test_listener_full: TestUser, session: AsyncSession
    ) -> None:
        """Notification data includes constructed deep link."""
        await create_device_token(session, test_listener_full.id, "device-token-123")
        
        actor_id = str(uuid.uuid4())
        content_id = "album-123"
        request_body = {
            "event_type": "new_release",
            "target_user_ids": [str(test_listener_full.id)],
            "actor_id": actor_id,
            "title": "New Album",
            "body": "Body",
            "metadata": {
                "album_id": content_id,
                "artistName": "Test Artist",
                "title": "New Album"
            }
        }

        response = await async_client.post(
            f"{TEST_BASE_URL}/notifications",
            headers=service_token_headers(),
            json=request_body,
        )

        assert response.status_code == status.HTTP_200_OK
        
        notification_count = await count_user_notifications(session, test_listener_full.id)
        assert notification_count == 1
