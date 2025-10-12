from typing import List

from pydantic import BaseModel, ConfigDict

from app.schemas.user import to_camel



class ArtistPublicProfile(BaseModel):
    username: str | None
    full_name: str | None
    profile_photo: str | None
    bio: str | None
    followers_count: int
    following_count: int
    photos: List[str]
    links: List[str]

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="forbid",
        from_attributes=True,
    )


class SocialLinksUpdateRequest(BaseModel):
    links: List[str]


class ArtistPhotosUpdateRequest(BaseModel):
    photos: List[str]


class DeletePhotoRequest(BaseModel):
    photo_url: str
