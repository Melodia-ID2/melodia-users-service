from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel

from app.models.regions import Country


class UserAccountStatus(str, Enum):
    ACTIVE = "active"
    BLOCKED = "blocked"

class UserRole(str, Enum):
    LISTENER = "listener"
    ARTIST = "artist"

class AccountProvider(str, Enum):
    LOCAL = "local"
    GOOGLE = "google"

class UserAccount(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    email: str = Field(index=True, unique=True, nullable=False)
    password: str | None = Field(nullable=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_login: datetime | None = Field(default=None)
    role: UserRole = Field(default=UserRole.LISTENER, nullable=False)
    status: UserAccountStatus = Field(default=UserAccountStatus.ACTIVE, nullable=False)
    country: Country = Field(default=Country.AR, nullable=False)
    is_profile_completed: bool = Field(default=False)
    provider: AccountProvider = Field(default=AccountProvider.LOCAL, nullable=False)
