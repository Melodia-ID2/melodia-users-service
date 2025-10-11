from uuid import UUID

from fastapi import APIRouter, Depends, File, UploadFile
from sqlmodel import Session

import app.controllers.users_controller as controller
from app.core.database import get_session
from app.core.security import get_current_user_id
from app.schemas.artist import ArtistPhotosUpdateRequest, ArtistPublicProfile, DeletePhotoRequest, SocialLinksUpdateRequest

router = APIRouter(prefix="/users/artist", tags=["Artists"])


@router.get("/{artist_id}", response_model=ArtistPublicProfile)
def get_artist(artist_id: UUID, session: Session = Depends(get_session)):
    return controller.get_artist(session, artist_id)


@router.put("/social-links", status_code=204)
def update_artist_social_links(
    data: SocialLinksUpdateRequest,
    session: Session = Depends(get_session),
    user_id: UUID = Depends(get_current_user_id),
):
    return controller.update_artist_social_links(session, user_id, data)


@router.put("/photos", status_code=201)
async def add_artist_photo(
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
    user_id: UUID = Depends(get_current_user_id),
):
    return await controller.add_artist_photo(session, user_id, file)


@router.delete("/photos", status_code=200)
def delete_artist_photo(
    data: DeletePhotoRequest,
    session: Session = Depends(get_session),
    user_id: UUID = Depends(get_current_user_id),
):
    return controller.delete_artist_photo(session, user_id, data.photo_url)


@router.put("/photos/reorder", status_code=200)
def reorder_artist_photos(
    data: ArtistPhotosUpdateRequest,
    session: Session = Depends(get_session),
    user_id: UUID = Depends(get_current_user_id),
):
    return controller.reorder_artist_photos(session, user_id, data.photos)
