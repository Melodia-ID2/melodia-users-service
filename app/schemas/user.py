from uuid import UUID
from pydantic import BaseModel, ConfigDict
from datetime import datetime

from typing import Optional
from app.models.user import UserRole, UserGender


def _to_camel(string: str) -> str:
    parts = string.split("_")
    return parts[0] + "".join(word.capitalize() for word in parts[1:])


class _UserProfilePayload(BaseModel):
    username: Optional[str] = None
    full_name: str
    birthdate: datetime | None = None
    role: UserRole
    gender: UserGender

    model_config = ConfigDict(
        alias_generator=_to_camel,
        populate_by_name=True,
        extra="forbid",
        from_attributes=True,
    )


class UserProfileCreate(_UserProfilePayload):
    pass

class UserProfileResponse(_UserProfilePayload):
    id: UUID
