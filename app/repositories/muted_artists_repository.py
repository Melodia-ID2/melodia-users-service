from uuid import UUID

from sqlmodel import Session, select

from app.models.user_muted_artist import UserMutedArtist


def list_muted_artists(session: Session, user_id: UUID) -> list[UUID]:
    stmt = select(UserMutedArtist.artist_id).where(UserMutedArtist.user_id == user_id)
    rows = session.exec(stmt).all()
    return list(rows)
