from typing import Union
from uuid import UUID

from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from sqlmodel import Session

import app.services.users_service as service
from app.core.database import get_session
from app.core.security import get_current_user_id
from app.schemas.message import MessageResponse
from app.schemas.profile_photo import ProfilePhotoResponse
from app.schemas.user import ArtistProfileResponse, FollowsListResponse, ListenerProfileView, SearchUsersResponse, UserProfileCreate, UserProfileResponse, UserProfileUpdate

router = APIRouter(prefix="", tags=["Users (Listeners & Artists)"])


@router.get("/me", response_model=Union[UserProfileResponse, ArtistProfileResponse])
def get_me(
    session: Session = Depends(get_session),
    user_id: UUID = Depends(get_current_user_id),
):
    return service.get_me(session, user_id)


@router.put("/me", response_model=UserProfileResponse)
async def update_me(
    data: UserProfileUpdate,
    session: Session = Depends(get_session),
    user_id: UUID = Depends(get_current_user_id),
):
    return await service.update_me(session, user_id, data)


@router.get("/search", response_model=SearchUsersResponse, status_code=status.HTTP_200_OK)
def search_users(
    query: str = Query(..., min_length=1),
    role: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: Session = Depends(get_session),
):
    return service.search_users(session, query, role, page, page_size)


@router.post("/profile", status_code=status.HTTP_201_CREATED)
async def create_user_profile(
    profile_data: UserProfileCreate,
    session: Session = Depends(get_session),
    user_id: UUID = Depends(get_current_user_id),
):
    return await service.create_user_profile(session, user_id, profile_data)


@router.post("/photo-profile", response_model=ProfilePhotoResponse)
async def update_profile_picture(
    file: UploadFile = File(...),
    current_user_id: UUID = Depends(get_current_user_id),
    session: Session = Depends(get_session),
):
    file_bytes = await file.read()
    return await service.update_profile_picture(session, current_user_id, file_bytes)


@router.get("/{user_id}/profile", response_model=ListenerProfileView)
def visualize_user(user_id: UUID, session: Session = Depends(get_session), current_user_id: UUID = Depends(get_current_user_id)):
    return service.visualize_user(session, user_id, current_user_id)


@router.post("/{user_id}/follow", response_model=MessageResponse, status_code=status.HTTP_200_OK)
def follow_user(user_id: UUID, session: Session = Depends(get_session), current_user_id: UUID = Depends(get_current_user_id)):
    return service.follow_user(session, current_user_id, user_id)


@router.get("/{user_id}/followers", response_model=FollowsListResponse, status_code=status.HTTP_200_OK)
def get_followers(user_id: UUID, session: Session = Depends(get_session), current_user_id: UUID = Depends(get_current_user_id)):
    return service.get_followers(session, user_id, current_user_id)


@router.get("/{user_id}/following", response_model=FollowsListResponse, status_code=status.HTTP_200_OK)
def get_following(user_id: UUID, session: Session = Depends(get_session), current_user_id: UUID = Depends(get_current_user_id)):
    return service.get_following(session, user_id, current_user_id)
