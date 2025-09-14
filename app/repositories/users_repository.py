from uuid import UUID
from sqlmodel import Session, select

from app.schemas.user import UserProfileCreate
from app.models.user import UserAccount, UserProfile


def get_all_users(session: Session):
    stmt = (
        select(
            UserProfile.id,
            UserProfile.username,
            UserAccount.email,
            UserProfile.role,
        ).join(UserAccount, UserProfile.id == UserAccount.id)  # type: ignore
    )
    return session.exec(stmt).all()


def get_profile_by_id(session: Session, user_id: UUID) -> UserProfile | None:
    return session.get(UserProfile, user_id)

def get_user_account_by_id(session: Session, user_id: UUID) -> UserAccount | None:
    return session.get(UserAccount, user_id)

def create_user_profile(
    session: Session, user_id: UUID, profile_data: UserProfileCreate
) -> UserProfile:
    new_profile = UserProfile(id=user_id, **profile_data.model_dump())
    session.add(new_profile)
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