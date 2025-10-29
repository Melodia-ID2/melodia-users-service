from uuid import UUID

from sqlalchemy.orm import aliased
from sqlmodel import Session, and_, func, select, update

from app.constants.notification_flags import NOTIFICATION_BITS_MASK
from app.models.useraccount import UserAccount
from app.models.userprofile import UserFollows, UserProfile


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

def change_history_preferences(session: Session, user_id: UUID):
    account = session.get(UserAccount, user_id)
    if not account:
        return None

    account.preferences ^= 0b1
    session.commit()
    session.refresh(account)

    return account


def get_user_preferences(session: Session, user_id: UUID) -> int | None:
    stmt = select(UserAccount.preferences).where(UserAccount.id == user_id)
    return session.exec(stmt).one_or_none()


def update_notification_preferences(session: Session, user_id: UUID, new_preferences: int) -> UserAccount | None:
    account = session.get(UserAccount, user_id)
    if not account:
        return None

    account.preferences = (account.preferences & ~NOTIFICATION_BITS_MASK) | (new_preferences & NOTIFICATION_BITS_MASK)

    session.add(account)
    session.commit()
    session.refresh(account)

    return account
