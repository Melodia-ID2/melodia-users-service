from typing import List

from pydantic import field_validator

from app.schemas.base import ApiBaseModel


class PreferredGenresUpdate(ApiBaseModel):
    genres: List[str]

    @field_validator('genres')
    @classmethod
    def validate_genres(cls, v: List[str]) -> List[str]:
        if len(v) > 5:
            raise ValueError('Maximum 5 genres allowed')
        return [g.upper() for g in v]


class PreferredGenresResponse(ApiBaseModel):
    genres: List[str]
