from pydantic import BaseModel


class PhotoProfileResponse(BaseModel):
    photo_profile: str
