from datetime import datetime
from uuid import UUID
from typing import Any
from app.schemas.base import ApiBaseModel
from app.models.notification import NotificationType


class NotificationPreferencesResponse(ApiBaseModel):
    new_releases: bool
    follow_activity: bool
    shared_content: bool
    new_followers: bool
    playlist_likes: bool


class NotificationPreferencesUpdate(ApiBaseModel):
    new_releases: bool
    follow_activity: bool
    shared_content: bool
    new_followers: bool
    playlist_likes: bool


class NotificationResponse(ApiBaseModel):
    id: UUID
    user_id: UUID
    type: NotificationType
    title: str
    body: str
    image_url: str | None
    data: dict[str, Any]
    created_at: datetime
    sent_at: datetime | None
    read_at: datetime | None
    clicked_at: datetime | None


class NotificationsListResponse(ApiBaseModel):
    notifications: list[NotificationResponse]
    total: int
    limit: int
    offset: int


class UnreadCountResponse(ApiBaseModel):
    count: int


class MarkAsReadResponse(ApiBaseModel):
    success: bool
    count: int

