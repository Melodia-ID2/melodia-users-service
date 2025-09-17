from uuid import UUID

from app.errors.exceptions import NotFoundError
from app.models.user import UserAccountStatus, UserProfile, UserRole
from pydantic import ValidationError
from sqlmodel import Session

from app.schemas.user import UserDetailedInfo, UserProfileCreate, UserProfileResponse
import app.repositories.users_repository as repo


def get_all_users(session: Session) -> list[dict[str, str]]:
    users = repo.get_all_users(session)
    return [
        {"id": str(u[0]), "username": u[1], "email": u[2], "role": u[3], "status": u[4]} for u in users
    ]


def get_user(session: Session, user_id: UUID) -> UserDetailedInfo:
    user = repo.get_user_account_by_id(session, user_id)
    if not user:
        raise NotFoundError("User with id: {} not found".format(user_id))
    user_profile = repo.get_profile_by_id(session, user_id)
    return UserDetailedInfo(
        id=str(user.id),
        username=None if not user_profile else user_profile.username,
        email=user.email,
        role=user.role,
        status=user.status,
        full_name=None if not user_profile else user_profile.full_name,
        phone_number=None if not user_profile else user_profile.phone_number,
        address=None if not user_profile else user_profile.address,
        last_login=user.last_login,
        created_at=user.created_at,
    )


def create_user_profile(
    session: Session, user_id: UUID, profile_data: UserProfileCreate
) -> UserProfileResponse:
    existing_profile = repo.get_profile_by_id(session, user_id)
    if existing_profile:
        raise ValidationError("Profile already exists")
    new_profile = UserProfile(id=user_id, **profile_data.model_dump())
    new_profile = repo.create_user_profile(session, new_profile)
    print(new_profile)
    return UserProfileResponse.model_validate(new_profile)


def update_user_role(session: Session, user_id: UUID) -> UserDetailedInfo:
    user = repo.get_user_account_by_id(session, user_id)
    if not user:
        raise NotFoundError("User with id: {} not found".format(user_id))
    user_profile = repo.get_profile_by_id(session, user_id)
    user.role = UserRole.ARTIST if user.role == UserRole.LISTENER else UserRole.LISTENER
    _ = repo.create_user_account(session, user)
    username= None if not user_profile else user_profile.username
    return UserDetailedInfo(
        id=str(user.id),
        username=username,
        email=user.email,
        role=user.role,
        status=user.status,
        phone_number=None if not user_profile else user_profile.phone_number,
        address=None if not user_profile else user_profile.address,
        last_login=user.last_login,
        created_at=user.created_at,
    )


def delete_user(session: Session, user_id: UUID):
    account = repo.get_user_account_by_id(session, user_id)
    if not account:
        raise NotFoundError("User with id: {} not found".format(user_id))
    _= repo.delete_user_account(session, account)
    return None

def update_user_status(session: Session, user_id: UUID) -> UserDetailedInfo:
    user = repo.get_user_account_by_id(session, user_id)
    if not user:
        raise NotFoundError("User with id: {} not found".format(user_id))
    user.status = UserAccountStatus.ACTIVE if user.status == UserAccountStatus.BLOCKED else UserAccountStatus.BLOCKED
    _ = repo.create_user_account(session, user)
    user_profile = repo.get_profile_by_id(session, user_id)
    username= None if not user_profile else user_profile.username
    return UserDetailedInfo(
        id=str(user.id),
        username=username,
        email=user.email,
        role=user.role,
        status=user.status,
        phone_number=None if not user_profile else user_profile.phone_number,
        address=None if not user_profile else user_profile.address,
        last_login=user.last_login,
        created_at=user.created_at,
    )