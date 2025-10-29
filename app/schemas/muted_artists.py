from uuid import UUID

from app.schemas.base import ApiBaseModel


class MutedArtistsListResponse(ApiBaseModel):
    muted_artists: list[UUID]
