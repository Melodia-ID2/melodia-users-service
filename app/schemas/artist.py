from typing import List
from pydantic import BaseModel, HttpUrl


class ArtistPublicProfile(BaseModel):
    username: str | None
    full_name: str | None
    photo_profile: str | None
    bio: str | None
    photos: List[str]
    links: List[str]

class SocialLinksUpdateRequest(BaseModel):
    links: List[str]

class ArtistPhotosUpdateRequest(BaseModel):
    photos: List[str]
    
class DeletePhotoRequest(BaseModel):
    photo_url: str