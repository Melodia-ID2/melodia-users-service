from uuid import UUID
from pydantic import BaseModel, ConfigDict
from pydantic.networks import HttpUrl


class PhotoProfileResponse(BaseModel):
    photo_profile: HttpUrl
