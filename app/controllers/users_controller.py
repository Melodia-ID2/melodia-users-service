from uuid import UUID
from sqlmodel import Session

from app.schemas.user import UserProfileCreate, UserProfileResponse, UserProfileUpdate
import app.services.users_service as service
from fastapi import UploadFile, File

def get_all_users(session: Session, page: int, page_size: int):
    return service.get_all_users(session, page, page_size)


def get_user(session: Session, user_id: UUID):
    return service.get_user(session, user_id)


def create_user_profile(session: Session, id: UUID, data: UserProfileCreate):
    return service.create_user_profile(session, id, data)


def update_user_role(session: Session, user_id: UUID):
    return service.update_user_role(session, user_id)

def delete_user(session: Session, user_id: UUID):
    service.delete_user(session, user_id)
    return None


async def update_photo_profile(session: Session,user_id: UUID, file: UploadFile = File(...)):
    file_bytes = await file.read()
    return service.update_photo_profile(session,user_id, file_bytes)

def get_me(session: Session, user_id: UUID):
    return service.get_me(session, user_id)


def search_users(session: Session, query: str, role: str | None, page: int, page_size: int):
    return service.search_users(session, query, role, page, page_size)


def update_me(session: Session, user_id: UUID, data: UserProfileUpdate) -> UserProfileResponse:
    return service.update_me(session, user_id, data)


def get_artist(session, artist_id):
    from app.services.users_service import get_artist as get_artist_service
    return service.get_artist(session, artist_id)

def visualize_user(session, user_id):
    return service.visualize_user(session, user_id)

def update_artist_social_links(session, user_id, data):
    return service.update_artist_social_links(session, user_id, data)

async def add_artist_photo(session: Session, user_id: UUID, file: UploadFile):
    file_bytes = await file.read()
    return service.add_artist_photo(session, user_id, file_bytes)