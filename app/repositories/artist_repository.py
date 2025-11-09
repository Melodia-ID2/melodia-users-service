from typing import List, Any, cast
from uuid import UUID

from sqlalchemy import func, desc
from sqlmodel import Session, delete, select

from app.models.useraccount import UserAccount, UserRole
from app.models.metricevent import MetricEvent, EventType
from app.models.userprofile import ArtistPhoto, SocialLink, UserProfile


def get_artist_photos(session: Session, artist_id: UUID):
    # Cast to Any to satisfy static typing for SQL expression methods
    return session.exec(select(ArtistPhoto).where(ArtistPhoto.artist_id == artist_id).order_by(cast(Any, ArtistPhoto.position))).all()


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


def get_artists_paginated(session: Session, page: int, page_size: int):
    popularity_subq = (
        select(
            cast(Any, MetricEvent.target_user_id).label("artist_id"),
            func.count(cast(Any, MetricEvent.id)).label("play_count"),
        )
        .where(MetricEvent.event_type == EventType.PLAY_SONG, cast(Any, MetricEvent.target_user_id).isnot(None))
        .group_by(cast(Any, MetricEvent.target_user_id))
        .subquery("popularity")
    )

    base = (
        select(UserProfile.id, UserProfile.username, UserProfile.profile_photo)
        .join(UserAccount, UserAccount.id == UserProfile.id)
        .join(popularity_subq, popularity_subq.c.artist_id == UserProfile.id, isouter=True)
        .where(UserAccount.role == UserRole.ARTIST)
    )

    total = session.exec(
        select(func.count())
        .select_from(
            select(UserProfile.id)
            .join(UserAccount, UserAccount.id == UserProfile.id)
            .where(UserAccount.role == UserRole.ARTIST)
            .subquery()
        )
    ).one()
    total_val = int(total or 0)

    stmt = (
        base.order_by(desc(func.coalesce(popularity_subq.c.play_count, 0)), UserProfile.username)
        .limit(page_size)
        .offset((page - 1) * page_size)
    )
    rows = session.exec(stmt).all()
    return rows, total_val
