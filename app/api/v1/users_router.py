from uuid import UUID
from fastapi import APIRouter, Depends, status
from app.schemas.user import UserProfileCreate
from sqlmodel import Session
from app.core.database import get_session
from app.core.security import get_current_user_id, require_admin

import app.controllers.users_controller as controller


router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", status_code=status.HTTP_200_OK)
def get_all_users(
    session: Session = Depends(get_session), _: None = Depends(require_admin)
):
    return controller.get_all_users(session)


@router.post("/profile", status_code=status.HTTP_201_CREATED)
def create_user_profile(
    profile_data: UserProfileCreate,
    session: Session = Depends(get_session),
    user_id: UUID = Depends(get_current_user_id),
):
    return controller.create_user_profile(session, user_id, profile_data)
