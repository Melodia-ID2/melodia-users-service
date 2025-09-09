from uuid import UUID
from fastapi import HTTPException
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
        raise HTTPException(status_code=400, detail="Profile already exists")

    new_profile = repo.create_user_profile(session, user_id, profile_data)
    return UserProfileResponse.model_validate(new_profile)
