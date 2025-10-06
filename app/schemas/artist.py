from typing import List
from pydantic import BaseModel


class ArtistPublicProfile(BaseModel):
    username: str | None
    full_name: str | None
    photo_profile: str | None
    bio: str | None
    photos: List[str]
    links: List[str]