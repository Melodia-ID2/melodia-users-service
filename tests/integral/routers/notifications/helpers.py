from datetime import datetime, timezone
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.devicetoken import DeviceToken
from app.models.notification import Notification
from app.models.user_muted_artist import UserMutedArtist


async def create_device_token(session: AsyncSession, user_id: UUID, token: str, is_active: bool = True) -> DeviceToken:
    """Create and persist a device token for testing."""
    device_token = DeviceToken(
        user_id=user_id,
        device_token=token,
        is_active=is_active,
        created_at=datetime.now(timezone.utc),
    )
    session.add(device_token)
    await session.commit()
    await session.refresh(device_token)
    return device_token


async def create_notification(
    session: AsyncSession,
    user_id: UUID,
    notification_type: str,
    title: str,
    body: str,
    data: dict | None = None,
    read_at: datetime | None = None,
    deleted_at: datetime | None = None,
) -> Notification:
    """Create and persist a notification for testing."""
    notification = Notification(
        user_id=user_id,
        type=notification_type,
        title=title,
        body=body,
        data=data or {},
        read_at=read_at,
        deleted_at=deleted_at,
    )
    session.add(notification)
    await session.commit()
    await session.refresh(notification)
    return notification


async def mute_artist(session: AsyncSession, user_id: UUID, artist_id: UUID) -> UserMutedArtist:
    """Mute an artist for a user."""
    muted = UserMutedArtist(
        user_id=user_id,
        artist_id=artist_id,
        created_at=datetime.utcnow(),
    )
    session.add(muted)
    await session.commit()
    await session.refresh(muted)
    return muted


async def get_notification_by_id(session: AsyncSession, notification_id: UUID) -> Notification | None:
    """Get notification by ID (bypassing session cache to see latest DB state)."""
    # Use get with execution_options to bypass the session cache
    result = await session.get(Notification, notification_id, options=[])
    if result:
        # Refresh to ensure we have the latest state from DB
        await session.refresh(result)
    return result


async def count_user_notifications(session: AsyncSession, user_id: UUID, include_deleted: bool = False) -> int:
    """Count notifications for a user."""
    query = select(Notification).where(Notification.user_id == user_id)
    if not include_deleted:
        query = query.where(Notification.deleted_at.is_(None))
    result = await session.execute(query)
    return len(result.scalars().all())


def expected_error_response(status: int, detail: str, instance: str) -> dict[str, str | int]:
    """Generate expected error response structure."""
    title_map = {
        401: "Authentication Error",
        403: "Forbidden",
        404: "Resource Not Found",
        400: "Bad request error",
        422: "Unprocessable Entity",
    }
    return {
        "type": "about:blank",
        "title": title_map.get(status, "Error"),
        "status": status,
        "detail": detail,
        "instance": instance,
    }


def service_token_headers() -> dict[str, str]:
    """Service-to-service authentication headers."""
    from app.core.config import settings
    return {"X-Service-Token": settings.SERVICE_TOKEN}
