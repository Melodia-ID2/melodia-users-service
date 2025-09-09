from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4
from sqlmodel import Field, SQLModel


class UserRole(Enum):
    LISTENER = "listener"
    ARTIST = "artist"


class UserAccount(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    email: str = Field(index=True, unique=True, nullable=False)
    password: str = Field(nullable=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class UserProfile(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    username: str = Field(index=True, unique=True, nullable=False)
    full_name: str | None = Field(default=None)
    birthdate: datetime | None = Field(default=None)
    role: UserRole = Field(default=UserRole.LISTENER, nullable=False)
