from datetime import date, datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict
from pydantic.networks import HttpUrl

from app.models.user import UserGender


def _to_camel(string: str) -> str:
    parts = string.split("_")
    return parts[0] + "".join(word.capitalize() for word in parts[1:])


class _UserProfilePayload(BaseModel):
    username: Optional[str] = None
    full_name: str
    birthdate: date | None = None
    gender: UserGender
    phone_number: str | None = None
    address: str | None = None
    profile_photo: HttpUrl | None = None
    bio: str | None = None
    followers_count: int = 0
    following_count: int = 0

    model_config = ConfigDict(
        alias_generator=_to_camel,
        populate_by_name=True,
        extra="forbid",
        from_attributes=True,
    )


class UserProfileUpdate(BaseModel):
    username: Optional[str] = None
    full_name: Optional[str] = None
    birthdate: Optional[date] = None
    gender: Optional[UserGender] = None
    phone_number: Optional[str] = None
    address: Optional[str] = None
    bio: Optional[str] = None

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


class ArtistProfileResponse(_UserProfilePayload):
    id: UUID
    photos: List[str] = []
    links: List[str] = []


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
    birthdate: date | None = None
    profile_photo: str | None = None
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
    role: str
    username: str | None = None
    profile_photo: str | None = None
    similarity_score: float

    model_config = ConfigDict(
        alias_generator=_to_camel,
        populate_by_name=True,
        extra="forbid",
        from_attributes=True,
    )


class ListenerPublicProfile(BaseModel):
    username: str | None
    photo_profile: str | None
    bio: str | None


class SearchUsersResponse(BaseModel):
    users: list[UserSearchItem]
