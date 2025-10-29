from uuid import UUID

from app.schemas.base import ApiBaseModel


class MuteArtistResponse(ApiBaseModel):
    artist_id: UUID


class MutedArtistsListResponse(ApiBaseModel):
    muted_artists: list[UUID]
