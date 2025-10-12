from typing import List

from app.schemas.base import ApiBaseModel


class ArtistPublicProfile(ApiBaseModel):
    username: str | None
    full_name: str | None
    profile_photo: str | None
    bio: str | None
    followers_count: int
    following_count: int
    photos: List[str]
    links: List[str]


class SocialLinksUpdateRequest(ApiBaseModel):
    links: List[str]


class ArtistPhotosUpdateRequest(ApiBaseModel):
    photos: List[str]


class DeletePhotoRequest(ApiBaseModel):
    photo_url: str
