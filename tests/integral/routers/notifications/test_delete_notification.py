import uuid
from datetime import datetime, timezone
import pytest
from httpx import AsyncClient
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import NotificationType
from tests.integral.conftest import TEST_BASE_URL, TestUser, auth_headers
from tests.integral.routers.notifications.helpers import (
    create_notification,
    count_user_notifications,
    expected_error_response,
)


@pytest.mark.asyncio
class TestDeleteNotification:
    """Tests for the DELETE /notifications/{id} endpoint."""

    async def test_delete_notification_success(
        self, async_client: AsyncClient, test_listener_full: TestUser, session: AsyncSession
    ) -> None:
        """Successfully soft delete a notification."""
        notif = await create_notification(
            session,
            test_listener_full.id,
            NotificationType.NEW_RELEASE.value,
            "Test Notification",
            "Test Body",
        )

        response = await async_client.delete(
            f"{TEST_BASE_URL}/notifications/{notif.id}",
            headers=auth_headers(test_listener_full.id, role="listener"),
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT

        await session.refresh(notif)
        assert notif.deleted_at is not None

    async def test_delete_notification_is_soft_delete(
        self, async_client: AsyncClient, test_listener_full: TestUser, session: AsyncSession
    ) -> None:
        """Delete is soft delete - record still exists in database."""
        notif = await create_notification(
            session,
            test_listener_full.id,
            NotificationType.NEW_RELEASE.value,
            "Test Notification",
            "Test Body",
        )

        await async_client.delete(
            f"{TEST_BASE_URL}/notifications/{notif.id}",
            headers=auth_headers(test_listener_full.id, role="listener"),
        )

        count = await count_user_notifications(session, test_listener_full.id, include_deleted=True)
        assert count == 1

        count_active = await count_user_notifications(session, test_listener_full.id, include_deleted=False)
        assert count_active == 0

    async def test_delete_notification_already_deleted(
        self, async_client: AsyncClient, test_listener_full: TestUser, session: AsyncSession
    ) -> None:
        """Deleting already deleted notification is idempotent."""
        notif = await create_notification(
            session,
            test_listener_full.id,
            NotificationType.NEW_RELEASE.value,
            "Test Notification",
            "Test Body",
            deleted_at=datetime.now(timezone.utc)
        )

        response = await async_client.delete(
            f"{TEST_BASE_URL}/notifications/{notif.id}",
            headers=auth_headers(test_listener_full.id, role="listener"),
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json() == expected_error_response(
            404,
            "Notificación no encontrada",
            f"/notifications/{notif.id}"
        )

    async def test_delete_notification_not_found(
        self, async_client: AsyncClient, test_listener_full: TestUser
    ) -> None:
        """Deleting non-existent notification fails."""
        nonexistent_id = uuid.uuid4()
        response = await async_client.delete(
            f"{TEST_BASE_URL}/notifications/{nonexistent_id}",
            headers=auth_headers(test_listener_full.id, role="listener"),
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json() == expected_error_response(
            404,
            "Notificación no encontrada",
            f"/notifications/{nonexistent_id}"
        )

    async def test_delete_notification_other_user_notification(
        self, async_client: AsyncClient, test_listener_full: TestUser, test_listener_minimal: TestUser, session: AsyncSession
    ) -> None:
        """Cannot delete another user's notification."""
        notif = await create_notification(
            session,
            test_listener_minimal.id,
            NotificationType.NEW_RELEASE.value,
            "Other User Notification",
            "Body",
        )

        response = await async_client.delete(
            f"{TEST_BASE_URL}/notifications/{notif.id}",
            headers=auth_headers(test_listener_full.id, role="listener"),
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

        await session.refresh(notif)
        assert notif.deleted_at is None

    async def test_delete_notification_hides_from_list(
        self, async_client: AsyncClient, test_listener_full: TestUser, session: AsyncSession
    ) -> None:
        """Deleted notification does not appear in GET list."""
        notif = await create_notification(
            session,
            test_listener_full.id,
            NotificationType.NEW_RELEASE.value,
            "Test Notification",
            "Test Body",
        )

        await async_client.delete(
            f"{TEST_BASE_URL}/notifications/{notif.id}",
            headers=auth_headers(test_listener_full.id, role="listener"),
        )

        list_response = await async_client.get(
            f"{TEST_BASE_URL}/notifications",
            headers=auth_headers(test_listener_full.id, role="listener"),
        )

        assert list_response.status_code == status.HTTP_200_OK
        assert list_response.json()["total"] == 0

    async def test_delete_notification_removes_from_unread_count(
        self, async_client: AsyncClient, test_listener_full: TestUser, session: AsyncSession
    ) -> None:
        """Deleted notification does not count as unread."""
        notif = await create_notification(
            session,
            test_listener_full.id,
            NotificationType.NEW_RELEASE.value,
            "Test Notification",
            "Test Body",
        )

        await async_client.delete(
            f"{TEST_BASE_URL}/notifications/{notif.id}",
            headers=auth_headers(test_listener_full.id, role="listener"),
        )

        count_response = await async_client.get(
            f"{TEST_BASE_URL}/notifications/unread-count",
            headers=auth_headers(test_listener_full.id, role="listener"),
        )

        assert count_response.status_code == status.HTTP_200_OK
        assert count_response.json()["count"] == 0

    async def test_delete_notification_unauthenticated(self, async_client: AsyncClient) -> None:
        """Request without authentication fails."""
        nonexistent_id = uuid.uuid4()
        response = await async_client.delete(f"{TEST_BASE_URL}/notifications/{nonexistent_id}")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json() == expected_error_response(
            401,
            "Token de autenticación invalido o no proporcionado",
            f"/notifications/{nonexistent_id}"
        )
