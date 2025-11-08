from datetime import datetime, timezone
from uuid import UUID, uuid4
from sqlmodel import Field, SQLModel


class DeviceToken(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="useraccount.id", ondelete="CASCADE", index=True, nullable=False)
    device_token: str = Field(nullable=False, unique=True, index=True)
    platform: str | None = Field(default=None)
    is_active: bool = Field(default=True, nullable=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime | None = Field(default=None)
