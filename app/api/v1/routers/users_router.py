from typing import Union
from uuid import UUID

from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from sqlmodel import Session

import app.controllers.users_controller as controller
from app.core.database import get_session
from app.core.security import get_current_user_id
from app.schemas.message import MessageResponse
from app.schemas.profile_photo import ProfilePhotoResponse
from app.schemas.user import ArtistProfileResponse, ListenerPublicProfile, SearchUsersResponse, UserProfileCreate, UserProfileResponse, UserProfileUpdate

router = APIRouter(prefix="/users", tags=["Users (Listeners & Artists)"])


@router.get("/me", response_model=Union[UserProfileResponse, ArtistProfileResponse])
def get_me(
    session: Session = Depends(get_session),
    user_id: UUID = Depends(get_current_user_id),
):
    return controller.get_me(session, user_id)


@router.put("/me", response_model=UserProfileResponse)
def update_me(
    data: UserProfileUpdate,
    session: Session = Depends(get_session),
    user_id: UUID = Depends(get_current_user_id),
):
    return controller.update_me(session, user_id, data)


@router.get("/search", response_model=SearchUsersResponse, status_code=status.HTTP_200_OK)
def search_users(
    query: str = Query(..., min_length=1),
    role: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: Session = Depends(get_session),
):
    return controller.search_users(session, query, role, page, page_size)


@router.post("/profile", status_code=status.HTTP_201_CREATED)
def create_user_profile(
    profile_data: UserProfileCreate,
    session: Session = Depends(get_session),
    user_id: UUID = Depends(get_current_user_id),
):
    return controller.create_user_profile(session, user_id, profile_data)


@router.post("/photo-profile", response_model=ProfilePhotoResponse)
async def update_profile_picture(
    file: UploadFile = File(...),
    current_user_id: UUID = Depends(get_current_user_id),
    session: Session = Depends(get_session),
):
    return await controller.update_profile_picture(session, current_user_id, file)


@router.get("/visualize/user/{user_id}", response_model=ListenerPublicProfile)
def visualize_user(user_id: UUID, session: Session = Depends(get_session)):
    return controller.visualize_user(session, user_id)


@router.get("/follow/{user_id}", response_model=MessageResponse, status_code=status.HTTP_200_OK)
def follow_user(user_id: UUID, session: Session = Depends(get_session), current_user_id: UUID = Depends(get_current_user_id)):
    return controller.follow_user(session, current_user_id, user_id)
