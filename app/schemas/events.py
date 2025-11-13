from uuid import UUID
from typing import Any
from pydantic import Field
from app.models.notification import NotificationType
from app.schemas.base import ApiBaseModel


class NotificationEventRequest(ApiBaseModel):
    event_type: NotificationType = Field(..., description="Type of notification event")
    actor_id: UUID | None = Field(None, description="User who performed the action (for NEW_RELEASE, this is the artist)")
    target_user_ids: list[UUID] = Field(..., description="List of user IDs to notify")
    title: str = Field(..., description="Notification title")
    body: str = Field(..., description="Notification body")
    image_url: str | None = Field(None, description="Optional image URL")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional event metadata to store in notification data")


class NotificationEventResponse(ApiBaseModel):
    notifications_created: int
    notifications_sent: int
    notifications_filtered: int
    filter_reasons: dict[str, int]
