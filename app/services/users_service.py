from uuid import UUID

from app.errors.exceptions import NotFoundError
from app.models.user import UserRole
from pydantic import ValidationError
from sqlmodel import Session

from app.schemas.user import UserProfileCreate, UserProfileResponse
import app.repositories.users_repository as repo


def get_all_users(session: Session) -> list[dict[str, str]]:
    users = repo.get_all_users(session)
    return [
        {"id": str(u[0]), "username": u[1], "email": u[2], "role": u[3]} for u in users
    ]


def create_user_profile(
    session: Session, user_id: UUID, profile_data: UserProfileCreate
) -> UserProfileResponse:
    existing_profile = repo.get_profile_by_id(session, user_id)
    if existing_profile:
        raise ValidationError("Profile already exists")

    new_profile = repo.create_user_profile(session, user_id, profile_data)
    return UserProfileResponse.model_validate(new_profile)


def update_user_role(session: Session, user_id: UUID):
    user = repo.get_user_account_by_id(session, user_id)
    if not user:
        raise NotFoundError("User with id: {} not found".format(user_id))
    user.role = UserRole.ARTIST if user.role == UserRole.LISTENER else UserRole.LISTENER
    _ = repo.create_user_account(session, user)
    return {
        "id": str(user.id),
        "username": user.username,
        "email": user.email,
        "role": user.role,
    }


def delete_user(session: Session, user_id: UUID):
    account = repo.get_user_account_by_id(session, user_id)
    if not account:
        raise NotFoundError("User with id: {} not found".format(user_id))
    _= repo.delete_user_account(session, account)
    return None