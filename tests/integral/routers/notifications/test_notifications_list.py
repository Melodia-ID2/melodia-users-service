from datetime import datetime, timezone
import pytest
from httpx import AsyncClient
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import NotificationType
from tests.integral.conftest import TEST_BASE_URL, TestUser, auth_headers
from tests.integral.routers.notifications.helpers import (
    create_notification,
    expected_error_response,
)


@pytest.mark.asyncio
class TestGetNotifications:
    """Tests for the GET /notifications endpoint."""

    async def test_get_notifications_empty_list(
        self, async_client: AsyncClient, test_listener_full: TestUser
    ) -> None:
        """Successfully retrieve empty notifications list."""
        response = await async_client.get(
            f"{TEST_BASE_URL}/notifications",
            headers=auth_headers(test_listener_full.id, role="listener"),
        )

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data["total"] == 0
        assert response_data["notifications"] == []

    async def test_get_notifications_with_results(
        self, async_client: AsyncClient, test_listener_full: TestUser, session: AsyncSession
    ) -> None:
        """Successfully retrieve notifications list."""
        notif1 = await create_notification(
            session,
            test_listener_full.id,
            NotificationType.NEW_RELEASE.value,
            "New Album",
            "Your favorite artist released a new album",
            {"contentId": "album-123", "deep_link": "com.melodia.is2://album/album-123"}
        )
        notif2 = await create_notification(
            session,
            test_listener_full.id,
            NotificationType.NEW_FOLLOWER.value,
            "New Follower",
            "Someone started following you",
            {"contentId": "user-456", "deep_link": "com.melodia.is2://user/user-456"}
        )

        response = await async_client.get(
            f"{TEST_BASE_URL}/notifications",
            headers=auth_headers(test_listener_full.id, role="listener"),
        )

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data["total"] == 2
        assert len(response_data["notifications"]) == 2
        
        notifications = response_data["notifications"]
        assert notifications[0]["type"] == NotificationType.NEW_FOLLOWER.value
        assert notifications[0]["title"] == "New Follower"
        assert notifications[0]["body"] == "Someone started following you"
        assert notifications[0]["data"]["deep_link"] == "com.melodia.is2://user/user-456"
        assert notifications[0]["readAt"] is None
        assert notifications[0]["clickedAt"] is None

        assert notifications[1]["type"] == NotificationType.NEW_RELEASE.value

    async def test_get_notifications_excludes_deleted(
        self, async_client: AsyncClient, test_listener_full: TestUser, session: AsyncSession
    ) -> None:
        """Deleted notifications are not returned."""
        await create_notification(
            session,
            test_listener_full.id,
            NotificationType.NEW_RELEASE.value,
            "Active Notification",
            "This is visible",
        )
        await create_notification(
            session,
            test_listener_full.id,
            NotificationType.NEW_FOLLOWER.value,
            "Deleted Notification",
            "This is hidden",
            deleted_at=datetime.now(timezone.utc)
        )

        response = await async_client.get(
            f"{TEST_BASE_URL}/notifications",
            headers=auth_headers(test_listener_full.id, role="listener"),
        )

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data["total"] == 1
        assert response_data["notifications"][0]["title"] == "Active Notification"

    async def test_get_notifications_pagination_default(
        self, async_client: AsyncClient, test_listener_full: TestUser, session: AsyncSession
    ) -> None:
        """Pagination works with default limit."""
        for i in range(25):
            await create_notification(
                session,
                test_listener_full.id,
                NotificationType.NEW_RELEASE.value,
                f"Notification {i}",
                f"Body {i}",
            )

        response = await async_client.get(
            f"{TEST_BASE_URL}/notifications",
            headers=auth_headers(test_listener_full.id, role="listener"),
        )

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data["total"] == 25
        assert len(response_data["notifications"]) == 20

    async def test_get_notifications_pagination_custom_limit(
        self, async_client: AsyncClient, test_listener_full: TestUser, session: AsyncSession
    ) -> None:
        """Pagination respects custom limit."""
        for i in range(15):
            await create_notification(
                session,
                test_listener_full.id,
                NotificationType.NEW_RELEASE.value,
                f"Notification {i}",
                f"Body {i}",
            )

        response = await async_client.get(
            f"{TEST_BASE_URL}/notifications?limit=5",
            headers=auth_headers(test_listener_full.id, role="listener"),
        )

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data["total"] == 15
        assert len(response_data["notifications"]) == 5

    async def test_get_notifications_pagination_with_offset(
        self, async_client: AsyncClient, test_listener_full: TestUser, session: AsyncSession
    ) -> None:
        """Pagination respects offset."""
        for i in range(10):
            await create_notification(
                session,
                test_listener_full.id,
                NotificationType.NEW_RELEASE.value,
                f"Notification {i}",
                f"Body {i}",
            )

        response = await async_client.get(
            f"{TEST_BASE_URL}/notifications?limit=5&offset=5",
            headers=auth_headers(test_listener_full.id, role="listener"),
        )

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data["total"] == 10
        assert len(response_data["notifications"]) == 5

    async def test_get_notifications_only_returns_own_notifications(
        self, async_client: AsyncClient, test_listener_full: TestUser, test_listener_minimal: TestUser, session: AsyncSession
    ) -> None:
        """User only sees their own notifications."""
        await create_notification(
            session,
            test_listener_full.id,
            NotificationType.NEW_RELEASE.value,
            "Full User Notification",
            "This is for full user",
        )
        await create_notification(
            session,
            test_listener_minimal.id,
            NotificationType.NEW_FOLLOWER.value,
            "Minimal User Notification",
            "This is for minimal user",
        )

        response = await async_client.get(
            f"{TEST_BASE_URL}/notifications",
            headers=auth_headers(test_listener_full.id, role="listener"),
        )

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data["total"] == 1
        assert response_data["notifications"][0]["title"] == "Full User Notification"

    async def test_get_notifications_unauthenticated(self, async_client: AsyncClient) -> None:
        """Request without authentication fails."""
        response = await async_client.get(f"{TEST_BASE_URL}/notifications")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json() == expected_error_response(
            401,
            "Token de autenticación invalido o no proporcionado",
            "/notifications"
        )


@pytest.mark.asyncio
class TestGetUnreadCount:
    """Tests for the GET /notifications/unread-count endpoint."""

    async def test_get_unread_count_zero(
        self, async_client: AsyncClient, test_listener_full: TestUser
    ) -> None:
        """Successfully retrieve zero unread count."""
        response = await async_client.get(
            f"{TEST_BASE_URL}/notifications/unread-count",
            headers=auth_headers(test_listener_full.id, role="listener"),
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"count": 0}

    async def test_get_unread_count_with_unread_notifications(
        self, async_client: AsyncClient, test_listener_full: TestUser, session: AsyncSession
    ) -> None:
        """Successfully retrieve count of unread notifications."""
        await create_notification(
            session,
            test_listener_full.id,
            NotificationType.NEW_RELEASE.value,
            "Unread 1",
            "Body",
        )
        await create_notification(
            session,
            test_listener_full.id,
            NotificationType.NEW_FOLLOWER.value,
            "Unread 2",
            "Body",
        )
        await create_notification(
            session,
            test_listener_full.id,
            NotificationType.PLAYLIST_LIKED.value,
            "Read Notification",
            "Body",
            read_at=datetime.now(timezone.utc)
        )

        response = await async_client.get(
            f"{TEST_BASE_URL}/notifications/unread-count",
            headers=auth_headers(test_listener_full.id, role="listener"),
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"count": 2}

    async def test_get_unread_count_excludes_deleted(
        self, async_client: AsyncClient, test_listener_full: TestUser, session: AsyncSession
    ) -> None:
        """Deleted notifications are not counted."""
        await create_notification(
            session,
            test_listener_full.id,
            NotificationType.NEW_RELEASE.value,
            "Unread Active",
            "Body",
        )
        await create_notification(
            session,
            test_listener_full.id,
            NotificationType.NEW_FOLLOWER.value,
            "Unread Deleted",
            "Body",
            deleted_at=datetime.now(timezone.utc)
        )

        response = await async_client.get(
            f"{TEST_BASE_URL}/notifications/unread-count",
            headers=auth_headers(test_listener_full.id, role="listener"),
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"count": 1}

    async def test_get_unread_count_only_counts_own_notifications(
        self, async_client: AsyncClient, test_listener_full: TestUser, test_listener_minimal: TestUser, session: AsyncSession
    ) -> None:
        """User only counts their own unread notifications."""
        await create_notification(
            session,
            test_listener_full.id,
            NotificationType.NEW_RELEASE.value,
            "Full User",
            "Body",
        )
        await create_notification(
            session,
            test_listener_minimal.id,
            NotificationType.NEW_FOLLOWER.value,
            "Minimal User",
            "Body",
        )

        response = await async_client.get(
            f"{TEST_BASE_URL}/notifications/unread-count",
            headers=auth_headers(test_listener_full.id, role="listener"),
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"count": 1}

    async def test_get_unread_count_unauthenticated(self, async_client: AsyncClient) -> None:
        """Request without authentication fails."""
        response = await async_client.get(f"{TEST_BASE_URL}/notifications/unread-count")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json() == expected_error_response(
            401,
            "Token de autenticación invalido o no proporcionado",
            "/notifications/unread-count"
        )
