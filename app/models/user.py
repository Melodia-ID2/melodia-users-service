from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4
from sqlmodel import Field, SQLModel


class UserRole(str, Enum):
    LISTENER = "listener"
    ARTIST = "artist"


class UserGender(Enum):
    FEMALE = "female"
    MALE = "male"
    NON_BINARY = "non_binary"
    OTHER = "other"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"


class UserAccountStatus(str, Enum):
    ACTIVE = "active"
    BLOCKED = "blocked"


class UserAccount(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    email: str = Field(index=True, unique=True, nullable=False)
    password: str = Field(nullable=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: UserAccountStatus = Field(default=UserAccountStatus.ACTIVE, nullable=False)


class UserProfile(SQLModel, table=True):
    id: UUID = Field(foreign_key="useraccount.id", primary_key=True, index=True, ondelete="CASCADE")
    username: str | None = Field(index=True, unique=True, nullable=True, default=None)
    full_name: str | None = Field(default=None)
    birthdate: datetime | None = Field(default=None)
    role: UserRole = Field(default=UserRole.LISTENER, nullable=False)
    gender: UserGender = Field(default=UserGender.PREFER_NOT_TO_SAY, nullable=False)

class RefreshToken(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="useraccount.id", ondelete="CASCADE", index=True, nullable=False)
    token: str = Field(nullable=False, unique=True)
    revoked: bool = Field(default=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))