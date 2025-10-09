from typing import Any
from uuid import UUID
from sqlmodel import Session, func, select, delete

from app.models.user import ArtistPhoto, SocialLink, UserAccount, UserProfile


def get_all_users(session: Session, page: int, page_size: int):
    stmt = (
        select(
            UserAccount.id,
            UserProfile.username,
            UserAccount.email,
            UserAccount.role,
            UserAccount.status,
        ).outerjoin(UserProfile, UserAccount.id == UserProfile.id)
        .order_by(UserAccount.created_at)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    users = session.exec(stmt).all()
    total = session.scalar(select(func.count()).select_from(UserAccount))
    return users, total


def search_users(session: Session, query: str, role: str | None, page: int, page_size: int) -> list[Any]:
    SIMILARITY_THRESHOLD = 0.3

    like_q = f"%{query}%"
    similarity_expr = func.similarity(UserProfile.username, query)
    cond = (
        (UserProfile.username.ilike(like_q)) |
        (similarity_expr > SIMILARITY_THRESHOLD)
    )

    if role:
        cond = cond & (UserAccount.role == role)
    
    stmt = (
        select(UserProfile.id, UserAccount.role, UserProfile.username, UserProfile.photo_profile)
        .join(UserAccount, UserProfile.id == UserAccount.id)
        .where(cond)
        .order_by(similarity_expr.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    users = session.exec(stmt).all()

    return users


def get_profile_by_id(session: Session, user_id: UUID) -> UserProfile | None:
    return session.get(UserProfile, user_id)

def get_user_account_by_id(session: Session, user_id: UUID) -> UserAccount | None:
    return session.get(UserAccount, user_id)

def get_profile_by_username(session: Session, username: str):
    return session.exec(select(UserProfile).where(UserProfile.username == username)).first()

def create_user_profile(
    session: Session, new_profile: UserProfile
) -> UserProfile:
    session.add(new_profile)
    
    user = session.get(UserAccount, new_profile.id)
    if user:
        user.is_profile_completed = True
        session.add(user)
    
    session.commit()
    session.refresh(new_profile)
    return new_profile

def create_user_account(session: Session, user: UserAccount) -> UserAccount:
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

def delete_user_account(session: Session, account: UserAccount) -> None:
    session.delete(account)
    session.commit()
    return None

def update_photo_profile(session: Session, user_id: UUID, photo_url: str) -> UserProfile | None:
    user_profile = session.get(UserProfile, user_id)
    if not user_profile:
        return None
    
    user_profile.photo_profile = photo_url
    session.add(user_profile)
    session.commit()
    session.refresh(user_profile)
    return user_profile

def get_user_profile_by_user_id(session: Session, user_id: UUID):
    return session.get(UserProfile, user_id)

def update_user_profile(session: Session, user_id: UUID, data: dict):
    profile = session.get(UserProfile, user_id)
    if not profile:
        return None
    for key, value in data.items():
        if hasattr(profile, key) and value is not None and getattr(profile, key) != value:
            setattr(profile, key, value)
    session.add(profile)
    session.commit()
    session.refresh(profile)
    return profile


def search_profiles(session: Session, query: str, role: str | None, page: int, page_size: int):
    stmt = select(UserProfile).outerjoin(UserAccount, UserAccount.id == UserProfile.id)
    if query:
        q = f"%{query}%"
        stmt = stmt.where((UserProfile.full_name.ilike(q)) | (UserProfile.username.ilike(q)))
    if role:
        stmt = stmt.where(UserAccount.role == role)
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    results = session.exec(stmt).all()
    return results

def get_artist_photos(session: Session, artist_id: UUID):
    return session.exec(
        select(ArtistPhoto)
        .where(ArtistPhoto.artist_id == artist_id)
        .order_by(ArtistPhoto.position)
    ).all()

def get_artist_links(session: Session, artist_id: UUID):
    return session.exec(
        select(SocialLink).where(SocialLink.artist_id == artist_id)
    ).all()

def delete_artist_social_links(session: Session, artist_id: UUID):
    stmt = delete(SocialLink).where(SocialLink.artist_id == artist_id)
    session.exec(stmt)

def add_artist_social_link(session: Session, artist_id: UUID, url: str):
    link = SocialLink(artist_id=artist_id, url=url)
    session.add(link)
    session.commit()

def delete_artist_photos(session: Session, artist_id: UUID):
    session.exec(
        select(ArtistPhoto).where(ArtistPhoto.artist_id == artist_id)
    ).delete(synchronize_session=False)
    session.commit()
    
def add_artist_photo(session: Session, artist_id: UUID, url: str, position: int):
    """Agregar una foto de artista"""
    photo = ArtistPhoto(
        artist_id=artist_id,
        url=url,
        position=position
    )
    session.add(photo)
    session.commit()
    session.refresh(photo)
    return photo

def get_artist_photos(session: Session, artist_id: UUID):
    """Obtener todas las fotos de un artista"""
    stmt = select(ArtistPhoto).where(ArtistPhoto.artist_id == artist_id)
    return session.exec(stmt).all()