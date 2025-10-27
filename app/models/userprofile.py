from datetime import date, datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class UserGender(str, Enum):
    FEMALE = "female"
    MALE = "male"
    NON_BINARY = "non_binary"
    OTHER = "other"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"


class UserProfile(SQLModel, table=True):
    id: UUID = Field(foreign_key="useraccount.id", primary_key=True, index=True, ondelete="CASCADE")
    username: str = Field(index=True, nullable=False)
    full_name: str = Field(nullable=False)
    birthdate: date = Field(nullable=False)
    gender: UserGender = Field(default=UserGender.PREFER_NOT_TO_SAY, nullable=False)
    phone_number: str | None = Field(default=None)
    address: str | None = Field(default=None)
    profile_photo: str | None = Field(default=None)
    bio: str | None = Field(default=None)
    following_count: int = Field(default=0, nullable=False)
    followers_count: int = Field(default=0, nullable=False)


class RefreshToken(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="useraccount.id", ondelete="CASCADE", index=True, nullable=False)
    token: str = Field(nullable=False, unique=True)
    revoked: bool = Field(default=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ArtistPhoto(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    artist_id: UUID = Field(foreign_key="useraccount.id", ondelete="CASCADE", nullable=False, index=True)
    url: str = Field(nullable=False)
    position: int = Field(nullable=False)
    uploaded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SocialLink(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    artist_id: UUID = Field(foreign_key="useraccount.id", ondelete="CASCADE", nullable=False, index=True)
    url: str = Field(nullable=False)


class UserFollows(SQLModel, table=True):
    follower_id: UUID = Field(foreign_key="useraccount.id", primary_key=True, index=True)
    followed_id: UUID = Field(foreign_key="useraccount.id", primary_key=True, index=True)
