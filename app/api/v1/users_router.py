from typing import Union
from uuid import UUID
from app.errors.error_responses import error_responses
from fastapi import APIRouter, Depends, Query, status, UploadFile, File, Request
from app.schemas.user import ArtistProfileResponse, GetAllUserResponse, ListenerPublicProfile, UserDetailedInfo, UserProfileCreate, UserProfileResponse, UserProfileUpdate, UserRoleUpdateResponse, SearchUsersResponse
from app.schemas.artist import ArtistPublicProfile, ArtistPhotosUpdateRequest
from app.schemas.artist import ArtistPublicProfile, SocialLinksUpdateRequest
from sqlmodel import Session
from app.core.database import get_session
from app.core.security import get_current_user_id, require_admin
import app.controllers.users_controller as controller
from app.schemas.photo_profile import PhotoProfileResponse

router = APIRouter(prefix="/users", tags=["users"])


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


@router.get("/", response_model=GetAllUserResponse, status_code=status.HTTP_200_OK, responses= error_responses(401))
def get_all_users(
    session: Session = Depends(get_session), _: None = Depends(require_admin), page: int = Query(1, ge=1), page_size: int = Query(10, ge=1, le=100),
):
    return controller.get_all_users(session, page, page_size)


@router.get("/search", response_model=SearchUsersResponse, status_code=status.HTTP_200_OK)
def search_users(
    query: str = Query(..., min_length=1),
    role: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: Session = Depends(get_session),
):
    return controller.search_users(session, query, role, page, page_size)


@router.get("/{user_id}", response_model=UserDetailedInfo, status_code=status.HTTP_200_OK, responses= error_responses(401, 404))
def get_user(
    user_id: UUID,
    session: Session = Depends(get_session),
    _: None = Depends(require_admin),
):
    return controller.get_user(session, user_id)


@router.patch("/{user_id}/role", response_model=UserRoleUpdateResponse, status_code=status.HTTP_200_OK, responses= error_responses(401, 404))
def update_user_role(
    user_id: UUID,
    session: Session = Depends(get_session),
    _: None = Depends(require_admin),
):
    return controller.update_user_role(session, user_id)


@router.post("/profile", status_code=status.HTTP_201_CREATED)
def create_user_profile(
    profile_data: UserProfileCreate,
    session: Session = Depends(get_session),
    user_id: UUID = Depends(get_current_user_id),
):
    return controller.create_user_profile(session, user_id, profile_data)

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT, responses= error_responses(401, 404))
def delete_user(
    user_id: UUID,
    session: Session = Depends(get_session),
    _: None = Depends(require_admin),
):
    return controller.delete_user(session, user_id)


@router.post("/photo-profile", response_model=PhotoProfileResponse)
async def update_photo_profile(
    file: UploadFile = File(...), 
    current_user_id: UUID = Depends(get_current_user_id),
    session: Session = Depends(get_session),
):
    return await controller.update_photo_profile(session,current_user_id, file)


@router.get("/artist/{artist_id}", response_model=ArtistPublicProfile)
def get_artist(
    artist_id: UUID,
    session: Session = Depends(get_session)
):
    return controller.get_artist(session, artist_id)


@router.get("/visualize/user/{user_id}", response_model=ListenerPublicProfile)
def visualize_user(
    user_id: UUID,
    session: Session = Depends(get_session)
):
    return controller.visualize_user(session, user_id)

@router.put("/artist/social-links", status_code=204)
def update_artist_social_links(
    data: SocialLinksUpdateRequest,
    session: Session = Depends(get_session),
    user_id: UUID = Depends(get_current_user_id),
):
    return controller.update_artist_social_links(session, user_id, data)

@router.put("/artist/photos", status_code=201)
async def add_artist_photo(
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
    user_id: UUID = Depends(get_current_user_id),
):
    return await controller.add_artist_photo(session, user_id, file)