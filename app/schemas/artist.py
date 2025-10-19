from typing import List

from app.schemas.base import ApiBaseModel
from app.schemas.user import UserProfilePublic


class ArtistProfileView(UserProfilePublic):
    is_following: bool = False
    photos: List[str]
    links: List[str]


class SocialLinksUpdateRequest(ApiBaseModel):
    links: List[str]


class ArtistPhotosUpdateRequest(ApiBaseModel):
    photos: List[str]


class DeletePhotoRequest(ApiBaseModel):
    photo_url: str
