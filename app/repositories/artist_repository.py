from typing import List
from uuid import UUID

from sqlmodel import Session, delete, select

from app.models.userprofile import ArtistPhoto, SocialLink


def get_artist_photos(session: Session, artist_id: UUID):
    return session.exec(select(ArtistPhoto).where(ArtistPhoto.artist_id == artist_id).order_by(ArtistPhoto.position)).all()


def get_artist_links(session: Session, artist_id: UUID):
    return session.exec(select(SocialLink).where(SocialLink.artist_id == artist_id)).all()


def update_artist_social_links(session: Session, artist_id: UUID, urls: List[str]):
    stmt = delete(SocialLink).where(SocialLink.artist_id == artist_id)
    session.exec(stmt)

    for url in urls:
        link = SocialLink(artist_id=artist_id, url=url)
        session.add(link)

    session.commit()


def delete_artist_photos(session: Session, artist_id: UUID):
    stmt = delete(ArtistPhoto).where(ArtistPhoto.artist_id == artist_id)
    session.exec(stmt)
    session.commit()


def add_artist_photo(session: Session, artist_id: UUID, url: str, position: int):
    """Agregar una foto de artista"""
    photo = ArtistPhoto(artist_id=artist_id, url=url, position=position)
    session.add(photo)
    session.commit()
    session.refresh(photo)
    return photo


def get_artist_photo_by_url(session: Session, artist_id: UUID, photo_url: str):
    stmt = select(ArtistPhoto).where(ArtistPhoto.artist_id == artist_id, ArtistPhoto.url == photo_url)
    return session.exec(stmt).first()


def delete_artist_photo(session: Session, artist_id: UUID, photo_url: str):
    stmt = delete(ArtistPhoto).where(ArtistPhoto.artist_id == artist_id, ArtistPhoto.url == photo_url)
    session.exec(stmt)
    session.commit()


def update_photo_position(session: Session, photo_id: UUID, new_position: int):
    stmt = select(ArtistPhoto).where(ArtistPhoto.id == photo_id)
    photo = session.exec(stmt).first()
    if photo:
        photo.position = new_position
        session.commit()


def update_photo_position_by_url(session: Session, artist_id: UUID, photo_url: str, new_position: int):
    stmt = select(ArtistPhoto).where(ArtistPhoto.artist_id == artist_id, ArtistPhoto.url == photo_url)
    photo = session.exec(stmt).first()
    if photo:
        photo.position = new_position
        session.commit()
