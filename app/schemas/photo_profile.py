from uuid import UUID
from pydantic import BaseModel, ConfigDict


class PhotoProfileResponse(BaseModel):
    photo_profile: str
