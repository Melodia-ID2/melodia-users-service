
from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlmodel import Session

from app.core.database import get_session
from app.core.security import get_current_user_id
import app.services.users_service as service
from app.schemas.message import MessageResponse
from app.schemas.notifications import NotificationPreferencesResponse, NotificationPreferencesUpdate


router = APIRouter(prefix="/preferences", tags=["Users Preferences"])

@router.patch("/history", status_code=status.HTTP_200_OK, response_model=MessageResponse)
def change_history_preferences(
    session: Session = Depends(get_session),
    user_id: UUID = Depends(get_current_user_id),
):
    return service.change_history_preferences(session, user_id)


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
