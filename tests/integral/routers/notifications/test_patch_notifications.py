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
    get_notification_by_id,
    expected_error_response,
)


@pytest.mark.asyncio
class TestMarkNotificationAsRead:
    """Tests for the PATCH /notifications/{id}/read endpoint."""

    async def test_patch_notification_read_success(
        self, async_client: AsyncClient, test_listener_full: TestUser, session: AsyncSession
    ) -> None:
        """Successfully mark notification as read."""
        notif = await create_notification(
            session,
            test_listener_full.id,
            NotificationType.NEW_RELEASE.value,
            "Test Notification",
            "Test Body",
        )

        response = await async_client.patch(
            f"{TEST_BASE_URL}/notifications/{notif.id}/read",
            headers=auth_headers(test_listener_full.id, role="listener"),
        )

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data["success"] is True
        assert response_data["count"] == 1

        updated = await get_notification_by_id(session, notif.id)
        assert updated is not None
        assert updated.read_at is not None

    async def test_patch_notification_read_already_read(
        self, async_client: AsyncClient, test_listener_full: TestUser, session: AsyncSession
    ) -> None:
        """Marking already read notification is idempotent."""
        notif = await create_notification(
            session,
            test_listener_full.id,
            NotificationType.NEW_RELEASE.value,
            "Test Notification",
            "Test Body",
            read_at=datetime.now(timezone.utc)
        )

        response = await async_client.patch(
            f"{TEST_BASE_URL}/notifications/{notif.id}/read",
            headers=auth_headers(test_listener_full.id, role="listener"),
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["success"] is True
        assert response.json()["count"] == 1

    async def test_patch_notification_read_not_found(
        self, async_client: AsyncClient, test_listener_full: TestUser
    ) -> None:
        """Marking non-existent notification fails."""
        nonexistent_id = uuid.uuid4()
        response = await async_client.patch(
            f"{TEST_BASE_URL}/notifications/{nonexistent_id}/read",
            headers=auth_headers(test_listener_full.id, role="listener"),
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json() == expected_error_response(
            404,
            "Notificación no encontrada",
            f"/notifications/{nonexistent_id}/read"
        )

    async def test_patch_notification_read_other_user_notification(
        self, async_client: AsyncClient, test_listener_full: TestUser, test_listener_minimal: TestUser, session: AsyncSession
    ) -> None:
        """Cannot mark another user's notification as read."""
        notif = await create_notification(
            session,
            test_listener_minimal.id,
            NotificationType.NEW_RELEASE.value,
            "Other User Notification",
            "Body",
        )

        response = await async_client.patch(
            f"{TEST_BASE_URL}/notifications/{notif.id}/read",
            headers=auth_headers(test_listener_full.id, role="listener"),
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_patch_notification_read_unauthenticated(self, async_client: AsyncClient) -> None:
        """Request without authentication fails."""
        nonexistent_id = uuid.uuid4()
        response = await async_client.patch(f"{TEST_BASE_URL}/notifications/{nonexistent_id}/read")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json() == expected_error_response(
            401,
            "Token de autenticación invalido o no proporcionado",
            f"/notifications/{nonexistent_id}/read"
        )


@pytest.mark.asyncio
class TestMarkAllNotificationsAsRead:
    """Tests for the PATCH /notifications/read-all endpoint."""

    async def test_patch_read_all_success(
        self, async_client: AsyncClient, test_listener_full: TestUser, session: AsyncSession
    ) -> None:
        """Successfully mark all notifications as read."""
        notif1 = await create_notification(
            session,
            test_listener_full.id,
            NotificationType.NEW_RELEASE.value,
            "Notification 1",
            "Body 1",
        )
        notif2 = await create_notification(
            session,
            test_listener_full.id,
            NotificationType.NEW_FOLLOWER.value,
            "Notification 2",
            "Body 2",
        )

        response = await async_client.patch(
            f"{TEST_BASE_URL}/notifications/read-all",
            headers=auth_headers(test_listener_full.id, role="listener"),
        )

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data["success"] is True
        assert response_data["count"] == 2

        updated1 = await get_notification_by_id(session, notif1.id)
        updated2 = await get_notification_by_id(session, notif2.id)
        assert updated1.read_at is not None
        assert updated2.read_at is not None

    async def test_patch_read_all_no_notifications(
        self, async_client: AsyncClient, test_listener_full: TestUser
    ) -> None:
        """Marking all as read when no notifications succeeds."""
        response = await async_client.patch(
            f"{TEST_BASE_URL}/notifications/read-all",
            headers=auth_headers(test_listener_full.id, role="listener"),
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["success"] is True
        assert response.json()["count"] == 0

    async def test_patch_read_all_already_read(
        self, async_client: AsyncClient, test_listener_full: TestUser, session: AsyncSession
    ) -> None:
        """Marking all as read when already read is idempotent."""
        await create_notification(
            session,
            test_listener_full.id,
            NotificationType.NEW_RELEASE.value,
            "Notification",
            "Body",
            read_at=datetime.now(timezone.utc)
        )

        response = await async_client.patch(
            f"{TEST_BASE_URL}/notifications/read-all",
            headers=auth_headers(test_listener_full.id, role="listener"),
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["success"] is True

    async def test_patch_read_all_only_affects_own_notifications(
        self, async_client: AsyncClient, test_listener_full: TestUser, test_listener_minimal: TestUser, session: AsyncSession
    ) -> None:
        """Only marks current user's notifications as read."""
        notif_full = await create_notification(
            session,
            test_listener_full.id,
            NotificationType.NEW_RELEASE.value,
            "Full User",
            "Body",
        )
        notif_minimal = await create_notification(
            session,
            test_listener_minimal.id,
            NotificationType.NEW_FOLLOWER.value,
            "Minimal User",
            "Body",
        )

        response = await async_client.patch(
            f"{TEST_BASE_URL}/notifications/read-all",
            headers=auth_headers(test_listener_full.id, role="listener"),
        )

        assert response.status_code == status.HTTP_200_OK

        updated_full = await get_notification_by_id(session, notif_full.id)
        updated_minimal = await get_notification_by_id(session, notif_minimal.id)
        assert updated_full.read_at is not None
        assert updated_minimal.read_at is None

    async def test_patch_read_all_unauthenticated(self, async_client: AsyncClient) -> None:
        """Request without authentication fails."""
        response = await async_client.patch(f"{TEST_BASE_URL}/notifications/read-all")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json() == expected_error_response(
            401,
            "Token de autenticación invalido o no proporcionado",
            "/notifications/read-all"
        )


@pytest.mark.asyncio
class TestMarkNotificationAsClicked:
    """Tests for the PATCH /notifications/{id}/clicked endpoint."""

    async def test_patch_notification_clicked_success(
        self, async_client: AsyncClient, test_listener_full: TestUser, session: AsyncSession
    ) -> None:
        """Successfully mark notification as clicked."""
        notif = await create_notification(
            session,
            test_listener_full.id,
            NotificationType.NEW_RELEASE.value,
            "Test Notification",
            "Test Body",
        )

        response = await async_client.patch(
            f"{TEST_BASE_URL}/notifications/{notif.id}/clicked",
            headers=auth_headers(test_listener_full.id, role="listener"),
        )

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data["success"] is True
        assert response_data["count"] == 1

        updated = await get_notification_by_id(session, notif.id)
        assert updated is not None
        assert updated.clicked_at is not None

    async def test_patch_notification_clicked_also_marks_as_read(
        self, async_client: AsyncClient, test_listener_full: TestUser, session: AsyncSession
    ) -> None:
        """Clicking notification also marks it as read."""
        notif = await create_notification(
            session,
            test_listener_full.id,
            NotificationType.NEW_RELEASE.value,
            "Test Notification",
            "Test Body",
        )

        response = await async_client.patch(
            f"{TEST_BASE_URL}/notifications/{notif.id}/clicked",
            headers=auth_headers(test_listener_full.id, role="listener"),
        )

        assert response.status_code == status.HTTP_200_OK

        updated = await get_notification_by_id(session, notif.id)
        assert updated.clicked_at is not None
        assert updated.read_at is not None

    async def test_patch_notification_clicked_already_clicked(
        self, async_client: AsyncClient, test_listener_full: TestUser, session: AsyncSession
    ) -> None:
        """Marking already clicked notification is idempotent."""
        notif = await create_notification(
            session,
            test_listener_full.id,
            NotificationType.NEW_RELEASE.value,
            "Test Notification",
            "Test Body",
        )
        
        await async_client.patch(
            f"{TEST_BASE_URL}/notifications/{notif.id}/clicked",
            headers=auth_headers(test_listener_full.id, role="listener"),
        )

        response = await async_client.patch(
            f"{TEST_BASE_URL}/notifications/{notif.id}/clicked",
            headers=auth_headers(test_listener_full.id, role="listener"),
        )

        assert response.status_code == status.HTTP_200_OK

    async def test_patch_notification_clicked_not_found(
        self, async_client: AsyncClient, test_listener_full: TestUser
    ) -> None:
        """Marking non-existent notification as clicked fails."""
        nonexistent_id = uuid.uuid4()
        response = await async_client.patch(
            f"{TEST_BASE_URL}/notifications/{nonexistent_id}/clicked",
            headers=auth_headers(test_listener_full.id, role="listener"),
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json() == expected_error_response(
            404,
            "Notificación no encontrada",
            f"/notifications/{nonexistent_id}/clicked"
        )

    async def test_patch_notification_clicked_other_user_notification(
        self, async_client: AsyncClient, test_listener_full: TestUser, test_listener_minimal: TestUser, session: AsyncSession
    ) -> None:
        """Cannot mark another user's notification as clicked."""
        notif = await create_notification(
            session,
            test_listener_minimal.id,
            NotificationType.NEW_RELEASE.value,
            "Other User Notification",
            "Body",
        )

        response = await async_client.patch(
            f"{TEST_BASE_URL}/notifications/{notif.id}/clicked",
            headers=auth_headers(test_listener_full.id, role="listener"),
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_patch_notification_clicked_unauthenticated(self, async_client: AsyncClient) -> None:
        """Request without authentication fails."""
        nonexistent_id = uuid.uuid4()
        response = await async_client.patch(f"{TEST_BASE_URL}/notifications/{nonexistent_id}/clicked")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json() == expected_error_response(
            401,
            "Token de autenticación invalido o no proporcionado",
            f"/notifications/{nonexistent_id}/clicked"
        )
