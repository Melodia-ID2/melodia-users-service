from uuid import UUID
from sqlmodel import Session

from app.schemas.user import UserProfileCreate, UserProfileResponse, UserProfileUpdate
import app.services.users_service as service
from fastapi import UploadFile, File

def get_all_users(session: Session):
    return {"users": service.get_all_users(session)}


def get_user(session: Session, user_id: UUID):
    return service.get_user(session, user_id)


def create_user_profile(session: Session, id: UUID, data: UserProfileCreate):
    return service.create_user_profile(session, id, data)


def update_user_role(session: Session, user_id: UUID):
    return service.update_user_role(session, user_id)

def delete_user(session: Session, user_id: UUID):
    service.delete_user(session, user_id)
    return None

def update_user_status(session: Session, user_id: UUID):
    return service.update_user_status(session, user_id)


async def update_photo_profile(session: Session,user_id: UUID, file: UploadFile = File(...)):
    file_bytes = await file.read()
    return service.update_photo_profile(session,user_id, file_bytes)

def get_me(session: Session, user_id: UUID) -> UserProfileResponse:
    return service.get_me(session, user_id)

def update_me(session: Session, user_id: UUID, data: UserProfileUpdate) -> UserProfileResponse:
    return service.update_me(session, user_id, data)