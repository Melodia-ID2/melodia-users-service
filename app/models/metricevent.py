from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4
from sqlmodel import Field, SQLModel


class EventType(str, Enum):
    PLAY_SONG = "play_song"
    FOLLOW_USER = "follow_user"
    SAVE_SONG = "save_song"
    SHARE_SONG = "share_song"
    PLAY_PLAYLIST = "play_playlist"
    LIKE_SONG = "like_song"
    REGISTER_USER = "register_user"


class MetricEvent(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    event_type: EventType = Field(index=True, nullable=False)
    user_id: UUID | None = Field(default=None, index=True)
    target_user_id: UUID | None = Field(default=None, index=True)
    song_id: str | None = Field(default=None, index=True, max_length=24)
    playlist_id: str | None = Field(default=None, index=True, max_length=24)
    region: str | None = Field(default=None, index=True)
    target_region: str | None = Field(default=None, index=True)
    timestamp: datetime = Field(default_factory=datetime.utcnow, index=True)