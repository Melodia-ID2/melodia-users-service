from uuid import UUID
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from pydantic.networks import HttpUrl

from typing import Optional
from app.models.user import UserGender


def _to_camel(string: str) -> str:
    parts = string.split("_")
    return parts[0] + "".join(word.capitalize() for word in parts[1:])


class _UserProfilePayload(BaseModel):
    username: Optional[str] = None
    full_name: str
    birthdate: datetime | None = None
    gender: UserGender
    phone_number: str | None = None
    address: str | None = None
    profile_photo: HttpUrl | None = None

    model_config = ConfigDict(
        alias_generator=_to_camel,
        populate_by_name=True,
        extra="forbid",
        from_attributes=True,
    )

class UserProfileUpdate(BaseModel):
    username: Optional[str] = None
    full_name: Optional[str] = None
    birthdate: Optional[datetime] = None
    gender: Optional[UserGender] = None
    phone_number: Optional[str] = None
    address: Optional[str] = None

    model_config = ConfigDict(
        alias_generator=_to_camel,
        populate_by_name=True,
        extra="forbid",
        from_attributes=True,
    )

class UserProfileCreate(_UserProfilePayload):
    pass

class UserProfileResponse(_UserProfilePayload):
    id: UUID

class UserBasicInfo(BaseModel):
    id: str
    email: str
    username: str | None = None
    role: str
    status: str

class UserDetailedInfo(UserBasicInfo):
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    address: Optional[str] = None
    birthdate: datetime | None = None
    profile_photo: HttpUrl | None = None
    last_login: Optional[datetime] = None
    created_at: Optional[datetime] = None 

    model_config = ConfigDict(
        alias_generator=_to_camel,
        populate_by_name=True,
        extra="forbid",
        from_attributes=True,
    )

class UserRoleUpdateResponse(BaseModel):
    id: str
    role: str

class GetAllUserResponse(BaseModel):
    users: list[UserBasicInfo]
    total: int
    page: int
    page_size: int
    total_pages: int


class UserSearchItem(BaseModel):
    id: str
    username: str | None = None
    profile_photo: str | None = None

    model_config = ConfigDict(
        alias_generator=_to_camel,
        populate_by_name=True,
        extra="forbid",
        from_attributes=True,
    )


class SearchUsersResponse(BaseModel):
    users: list[UserSearchItem]
