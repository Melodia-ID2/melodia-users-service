from datetime import date, datetime
from typing import List, Optional
from uuid import UUID

from pydantic.networks import HttpUrl

from app.models.user import UserGender
from app.schemas.base import ApiBaseModel


class _UserProfilePayload(ApiBaseModel):
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


class UserProfileUpdate(ApiBaseModel):
    username: Optional[str] = None
    full_name: Optional[str] = None
    birthdate: Optional[date] = None
    gender: Optional[UserGender] = None
    phone_number: Optional[str] = None
    address: Optional[str] = None
    bio: Optional[str] = None


class UserProfileCreate(_UserProfilePayload):
    pass


class UserProfileResponse(_UserProfilePayload):
    id: UUID


class ArtistProfileResponse(UserProfileResponse):
    photos: List[str] = []
    links: List[str] = []


class UserBasicInfo(ApiBaseModel):
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


class UserRoleUpdateResponse(ApiBaseModel):
    id: str
    role: str


class GetAllUserResponse(ApiBaseModel):
    users: list[UserBasicInfo]
    total: int
    page: int
    page_size: int
    total_pages: int


class UserSearchItem(ApiBaseModel):
    id: str
    role: str
    username: str | None = None
    profile_photo: str | None = None
    similarity_score: float


class UserProfilePublic(ApiBaseModel):
    username: str | None
    profile_photo: str | None
    bio: str | None
    followers_count: int
    following_count: int


class ListenerProfileView(UserProfilePublic):
    is_following: bool = False


class SearchUsersResponse(ApiBaseModel):
    users: list[UserSearchItem]
