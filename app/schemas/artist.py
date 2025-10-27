from typing import List

from app.schemas.base import ApiBaseModel


class SocialLinksUpdateRequest(ApiBaseModel):
    links: List[str]


class ArtistPhotosUpdateRequest(ApiBaseModel):
    photos: List[str]


class DeletePhotoRequest(ApiBaseModel):
    photo_url: str
