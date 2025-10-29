from uuid import UUID

from sqlmodel import Session, select

from app.models.user_muted_artist import UserMutedArtist


def list_muted_artists(session: Session, user_id: UUID) -> list[UUID]:
    stmt = select(UserMutedArtist.artist_id).where(UserMutedArtist.user_id == user_id)
    rows = session.exec(stmt).all()
    return list(rows)


def mute_artist(session: Session, user_id: UUID, artist_id: UUID) -> UserMutedArtist:
    existing = session.get(UserMutedArtist, (user_id, artist_id))
    if existing:
        return existing

    muted = UserMutedArtist(user_id=user_id, artist_id=artist_id)
    session.add(muted)
    session.commit()
    session.refresh(muted)
    return muted
