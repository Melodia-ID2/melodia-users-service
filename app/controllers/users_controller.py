from uuid import UUID
from sqlmodel import Session

from app.schemas.user import UserProfileCreate
import app.services.users_service as service


def get_all_users(session: Session):
    return {"users": service.get_all_users(session)}


def create_user_profile(session: Session, id: UUID, data: UserProfileCreate):
    return {"user": service.create_user_profile(session, id, data)}


def update_user_role(session: Session, user_id: UUID):
    return {"user": service.update_user_role(session, user_id)}

def delete_user(session: Session, user_id: UUID):
    service.delete_user(session, user_id)
    return None