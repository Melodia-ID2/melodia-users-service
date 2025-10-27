from uuid import UUID

from fastapi import APIRouter, Depends, File, UploadFile
from sqlmodel import Session

import app.services.artist_service as service
from app.core.database import get_session
from app.core.security import get_current_user_id
from app.schemas.artist import ArtistPhotosUpdateRequest, DeletePhotoRequest, SocialLinksUpdateRequest

router = APIRouter(prefix="/artist", tags=["Artists"])


@router.put("/social-links", status_code=204)
def update_artist_social_links(
    data: SocialLinksUpdateRequest,
    session: Session = Depends(get_session),
    user_id: UUID = Depends(get_current_user_id),
):
    return service.update_artist_social_links(session, user_id, data)


@router.put("/photos", status_code=201)
async def add_artist_photo(
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
    user_id: UUID = Depends(get_current_user_id),
):
    file_bytes = await file.read()
    return service.add_artist_photo(session, user_id, file_bytes)


@router.delete("/photos", status_code=200)
def delete_artist_photo(
    data: DeletePhotoRequest,
    session: Session = Depends(get_session),
    user_id: UUID = Depends(get_current_user_id),
):
    return service.delete_artist_photo(session, user_id, data.photo_url)


@router.put("/photos/reorder", status_code=200)
def reorder_artist_photos(
    data: ArtistPhotosUpdateRequest,
    session: Session = Depends(get_session),
    user_id: UUID = Depends(get_current_user_id),
):
    return service.reorder_artist_photos(session, user_id, data.photos)
