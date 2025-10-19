from pydantic import BaseModel


class ProfilePhotoResponse(BaseModel):
    profile_photo: str
