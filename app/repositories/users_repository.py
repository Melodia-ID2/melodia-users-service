from typing import List
from uuid import UUID

from sqlalchemy.orm import aliased
from sqlmodel import Session, and_, case, delete, func, select, update

from app.models.useraccount import AccountProvider, UserAccount
from app.models.usercredential import UserCredential
from app.models.userprofile import ArtistPhoto, SocialLink, UserFollows, UserProfile


def get_all_users(session: Session, page: int, page_size: int):
    # Subquery: get one credential per user, preferring local provider
    subq = (
        select(
            UserCredential.email,
            UserCredential.provider,
            UserCredential.user_id,
            case((UserCredential.provider == AccountProvider.LOCAL, 1), else_=0).label("is_local"),
            func.row_number()
            .over(
                partition_by=UserCredential.user_id,
                order_by=case((UserCredential.provider == AccountProvider.LOCAL, 1), else_=0).desc(),
            )
            .label("rn"),
        )
        .subquery()
    )

    filtered_subq = select(subq).where(subq.c.rn == 1).subquery()

    # Main query
    stmt = (
        select(
            UserAccount.id,
            UserProfile.username,
            filtered_subq.c.email,
            UserAccount.role,
            UserAccount.status,
        )
        .outerjoin(UserProfile, UserAccount.id == UserProfile.id)
        .outerjoin(filtered_subq, UserAccount.id == filtered_subq.c.user_id)
        .order_by(UserAccount.created_at)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    users = session.exec(stmt).all()
    total = session.scalar(select(func.count()).select_from(UserAccount))
    return users, total


def search_users(session: Session, query: str, role: str | None, page: int, page_size: int):
    contains_boost = case((UserProfile.username.ilike(f"%{query}%"), 0.3), else_=0)
    prefix_boost = case((UserProfile.username.ilike(f"{query}%"), 0.2), else_=0)

    similarity_expr = func.similarity(UserProfile.username, query) + contains_boost + prefix_boost

    stmt = (
        select(UserProfile.id, UserAccount.role, UserProfile.username, UserProfile.profile_photo, similarity_expr.label("similarity_score"))
        .join(UserAccount, UserProfile.id == UserAccount.id)
        .order_by(similarity_expr.desc(), UserProfile.username.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    if role:
        stmt = stmt.where(UserAccount.role == role)

    return session.exec(stmt).all()


def get_profile_by_id(session: Session, user_id: UUID) -> UserProfile | None:
    return session.get(UserProfile, user_id)


def get_account_by_id(session: Session, user_id: UUID) -> UserAccount | None:
    return session.get(UserAccount, user_id)


def get_profile_by_username(session: Session, username: str):
    return session.exec(select(UserProfile).where(UserProfile.username == username)).first()


def create_user_profile(session: Session, new_profile: UserProfile) -> UserProfile:
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


def update_profile_picture(session: Session, user_id: UUID, photo_url: str) -> UserProfile | None:
    user_profile = session.get(UserProfile, user_id)
    if not user_profile:
        return None

    user_profile.profile_photo = photo_url
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
    return session.exec(select(ArtistPhoto).where(ArtistPhoto.artist_id == artist_id).order_by(ArtistPhoto.position)).all()


def get_artist_links(session: Session, artist_id: UUID):
    return session.exec(select(SocialLink).where(SocialLink.artist_id == artist_id)).all()


def update_artist_social_links(session: Session, artist_id: UUID, urls: List[str]):
    try:
        stmt = delete(SocialLink).where(SocialLink.artist_id == artist_id)
        session.exec(stmt)

        for url in urls:
            link = SocialLink(artist_id=artist_id, url=url)
            session.add(link)

        session.commit()

    except Exception as e:
        session.rollback()
        raise e


def delete_artist_photos(session: Session, artist_id: UUID):
    session.exec(select(ArtistPhoto).where(ArtistPhoto.artist_id == artist_id)).delete(synchronize_session=False)
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


def is_following(session: Session, follower_id: UUID, followed_id: UUID) -> bool:
    stmt = select(UserFollows).where(UserFollows.follower_id == follower_id, UserFollows.followed_id == followed_id)
    return session.exec(stmt).first() is not None


def toggle_follow(session: Session, follower_id: UUID, followed_id: UUID):
    stmt = select(UserFollows).where(UserFollows.follower_id == follower_id, UserFollows.followed_id == followed_id)
    is_following = session.exec(stmt).first()
    if is_following:
        session.delete(is_following)
        _bump_counter(session, follower_id, "following_count", -1)
        _bump_counter(session, followed_id, "followers_count", -1)
        return False
    else:
        new_follow = UserFollows(follower_id=follower_id, followed_id=followed_id)
        session.add(new_follow)
        _bump_counter(session, follower_id, "following_count", 1)
        _bump_counter(session, followed_id, "followers_count", 1)
        return True


def _bump_counter(session: Session, user_id: UUID, field: str, delta: int) -> None:
    session.exec(update(UserProfile).where(UserProfile.id == user_id).values({field: func.greatest(getattr(UserProfile, field) + delta, 0)}))


def get_followers(session: Session, user_id: UUID, current_user_id: UUID):
    FollowsCheck = aliased(UserFollows)

    stmt = (
        select(
            UserProfile.id,
            UserProfile.username,
            UserProfile.profile_photo,
            UserProfile.followers_count,
            UserAccount.country,
            (FollowsCheck.follower_id != None).label("is_following"),
        )
        .join(UserFollows, UserFollows.follower_id == UserProfile.id)
        .join(
            FollowsCheck,
            and_(
                FollowsCheck.follower_id == current_user_id,
                FollowsCheck.followed_id == UserProfile.id,
            ),
            isouter=True,
        )
        .where(UserFollows.followed_id == user_id)
        .order_by(UserProfile.username)
    )
    return session.exec(stmt).all()


def get_following(session: Session, user_id: UUID, current_user_id: UUID):
    FollowsCheck = aliased(UserFollows)

    stmt = (
        select(
            UserProfile.id,
            UserProfile.username,
            UserProfile.profile_photo,
            UserProfile.followers_count,
            UserAccount.country,
            (FollowsCheck.follower_id != None).label("is_following"),
        )
        .join(UserFollows, UserFollows.followed_id == UserProfile.id)
        .join(
            FollowsCheck,
            and_(
                FollowsCheck.follower_id == current_user_id,
                FollowsCheck.followed_id == UserProfile.id,
            ),
            isouter=True,
        )
        .where(UserFollows.follower_id == user_id)
        .order_by(UserProfile.username)
    )

    return session.exec(stmt).all()
