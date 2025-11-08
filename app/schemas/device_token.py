from datetime import datetime
from uuid import UUID
from pydantic import Field

from app.schemas.base import ApiBaseModel


class DeviceTokenRegisterRequest(ApiBaseModel):
    device_token: str = Field(..., min_length=1, description="FCM device token")
    platform: str | None = Field(None, description="Platform: android, ios, web")


class DeviceTokenResponse(ApiBaseModel):
    id: UUID
    user_id: UUID
    device_token: str
    platform: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime | None


class DeviceTokenListResponse(ApiBaseModel):
    tokens: list[DeviceTokenResponse]
    total: int
