from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4
from sqlmodel import Field, SQLModel, JSON, Column
from typing import Any


class NotificationType(str, Enum):
    NEW_RELEASE = "new_release"
    PLAYLIST_PUBLISHED = "playlist_published"
    CONTENT_SHARED = "content_shared"
    NEW_FOLLOWER = "new_follower"
    PLAYLIST_LIKED = "playlist_liked"


class Notification(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="useraccount.id", ondelete="CASCADE", index=True, nullable=False)
    type: NotificationType = Field(nullable=False, index=True)
    title: str = Field(nullable=False)
    body: str = Field(nullable=False)
    image_url: str | None = Field(default=None)
    data: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    sent_at: datetime | None = Field(default=None)
    read_at: datetime | None = Field(default=None, index=True)
    clicked_at: datetime | None = Field(default=None)
    deleted_at: datetime | None = Field(default=None, index=True)
