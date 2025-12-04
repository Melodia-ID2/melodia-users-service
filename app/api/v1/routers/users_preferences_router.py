
from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlmodel import Session

from app.core.database import get_session
from app.core.security import get_current_user_id
import app.services.users_service as service
from app.schemas.message import MessageResponse
from app.schemas.user import AutoplayPreferenceResponse
from app.schemas.notifications import NotificationPreferencesResponse, NotificationPreferencesUpdate
from app.schemas.muted_artists import MuteArtistResponse, MutedArtistsListResponse
from app.schemas.preferred_genres import PreferredGenresResponse, PreferredGenresUpdate


router = APIRouter(prefix="/preferences", tags=["Users Preferences"])

@router.patch("/history", status_code=status.HTTP_200_OK, response_model=MessageResponse)
def change_history_preferences(
    session: Session = Depends(get_session),
    user_id: UUID = Depends(get_current_user_id),
):
    return service.change_history_preferences(session, user_id)


@router.patch("/autoplay", status_code=status.HTTP_200_OK, response_model=AutoplayPreferenceResponse)
def change_autoplay_preferences(
    session: Session = Depends(get_session),
    user_id: UUID = Depends(get_current_user_id),
):
    return service.change_autoplay_preferences(session, user_id)


@router.get("/autoplay", status_code=status.HTTP_200_OK, response_model=AutoplayPreferenceResponse)
def get_autoplay_preferences(
    session: Session = Depends(get_session),
    user_id: UUID = Depends(get_current_user_id),
):
    return service.get_autoplay_preferences(session, user_id)


@router.get("/notifications", status_code=status.HTTP_200_OK, response_model=NotificationPreferencesResponse)
def get_notification_preferences(
    session: Session = Depends(get_session),
    user_id: UUID = Depends(get_current_user_id),
):
    return service.get_notification_preferences(session, user_id)


@router.put("/notifications", status_code=status.HTTP_200_OK, response_model=NotificationPreferencesResponse)
def update_notification_preferences(
    data: NotificationPreferencesUpdate,
    session: Session = Depends(get_session),
    user_id: UUID = Depends(get_current_user_id),
):
    return service.update_notification_preferences(session, user_id, data)


@router.get("/notifications/muted-artists", status_code=status.HTTP_200_OK, response_model=MutedArtistsListResponse)
def list_muted_artists(
    session: Session = Depends(get_session),
    user_id: UUID = Depends(get_current_user_id),
):
    return service.list_muted_artists(session, user_id)


@router.put("/notifications/muted-artists/{artist_id}", status_code=status.HTTP_200_OK, response_model=MuteArtistResponse)
def mute_artist(
    artist_id: UUID,
    session: Session = Depends(get_session),
    user_id: UUID = Depends(get_current_user_id),
):
    return service.mute_artist(session, user_id, artist_id)


@router.delete("/notifications/muted-artists/{artist_id}", status_code=status.HTTP_204_NO_CONTENT)
def unmute_artist(
    artist_id: UUID,
    session: Session = Depends(get_session),
    user_id: UUID = Depends(get_current_user_id),
):
    service.unmute_artist(session, user_id, artist_id)


@router.get("/genres", status_code=status.HTTP_200_OK, response_model=PreferredGenresResponse)
def get_preferred_genres(
    session: Session = Depends(get_session),
    user_id: UUID = Depends(get_current_user_id),
):
    """Get user's preferred genres."""
    return service.get_preferred_genres(session, user_id)


@router.put("/genres", status_code=status.HTTP_200_OK, response_model=PreferredGenresResponse)
def update_preferred_genres(
    data: PreferredGenresUpdate,
    session: Session = Depends(get_session),
    user_id: UUID = Depends(get_current_user_id),
):
    """Update user's preferred genres (max 5)."""
    return service.update_preferred_genres(session, user_id, data)
