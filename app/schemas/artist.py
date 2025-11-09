from typing import List

from app.schemas.base import ApiBaseModel


class SocialLinksUpdateRequest(ApiBaseModel):
    links: List[str]


class ArtistPhotosUpdateRequest(ApiBaseModel):
    photos: List[str]


class DeletePhotoRequest(ApiBaseModel):
    photo_url: str


class ArtistListItem(ApiBaseModel):
    id: str
    username: str | None = None
    profile_photo: str | None = None


class ArtistsListResponse(ApiBaseModel):
    artists: list[ArtistListItem]
    total: int
    page: int
    page_size: int
    total_pages: int
