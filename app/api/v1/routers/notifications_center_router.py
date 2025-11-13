from uuid import UUID
from fastapi import APIRouter, Depends, Query, Header, HTTPException, status
from sqlmodel import Session

from app.core.database import get_session
from app.core.security import get_current_user_id
from app.core.config import settings
from app.services import notification_service
from app.schemas.notifications import NotificationResponse, NotificationsListResponse, UnreadCountResponse, MarkAsReadResponse
from app.schemas.events import NotificationEventRequest, NotificationEventResponse
from app.services import event_service
from app.errors.exceptions import NotFoundError


router = APIRouter(prefix="/notifications", tags=["Notifications"])


def verify_service_token(x_service_token: str = Header(...)):
    """Service-to-service authentication via header token."""
    if x_service_token != settings.SERVICE_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid service token"
        )
    return True


@router.post("", status_code=status.HTTP_200_OK, response_model=NotificationEventResponse, dependencies=[Depends(verify_service_token)])
def create_notifications(
    event: NotificationEventRequest,
    session: Session = Depends(get_session),
):
    """Create notifications from external services."""
    stats = event_service.process_notification_event(
        session=session,
        event_type=event.event_type,
        title=event.title,
        body=event.body,
        target_user_ids=event.target_user_ids,
        actor_id=event.actor_id,
        image_url=event.image_url,
        metadata=event.metadata
    )
    
    return NotificationEventResponse(
        notifications_created=stats["notifications_created"],
        notifications_sent=stats["notifications_sent"],
        notifications_filtered=stats["notifications_filtered"],
        filter_reasons={
            "user_disabled": stats["filter_reasons"]["user_disabled"],
            "artist_muted": stats["filter_reasons"]["artist_muted"],
            "no_tokens": stats["filter_reasons"]["no_tokens"],
        },
    )


@router.get("", status_code=status.HTTP_200_OK, response_model=NotificationsListResponse)
def list_notifications(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    unread_only: bool = Query(False),
    session: Session = Depends(get_session),
    user_id: UUID = Depends(get_current_user_id),
):
    """Get paginated list of notifications for the current user."""
    notifications, total = notification_service.get_user_notifications(
        session=session,
        user_id=user_id,
        limit=limit,
        offset=offset,
        unread_only=unread_only,
    )
    
    return NotificationsListResponse(
        notifications=[NotificationResponse.model_validate(n) for n in notifications],
        total=total,
        limit=limit,
        offset=offset
    )


@router.get("/unread-count", status_code=status.HTTP_200_OK, response_model=UnreadCountResponse)
def get_unread_count(
    session: Session = Depends(get_session),
    user_id: UUID = Depends(get_current_user_id),
):
    """Get count of unread notifications."""
    count = notification_service.get_unread_count(session=session, user_id=user_id)
    return UnreadCountResponse(count=count)


@router.patch("/{notification_id}/read", status_code=status.HTTP_200_OK, response_model=MarkAsReadResponse)
def mark_notification_as_read(
    notification_id: UUID,
    session: Session = Depends(get_session),
    user_id: UUID = Depends(get_current_user_id),
):
    """Mark a single notification as read."""
    success = notification_service.mark_notification_as_read(
        session=session,
        user_id=user_id,
        notification_id=notification_id,
    )
    if not success:
        raise NotFoundError("Notificación no encontrada")
    return MarkAsReadResponse(success=True, count=1)


@router.patch("/read-all", status_code=status.HTTP_200_OK, response_model=MarkAsReadResponse)
def mark_all_as_read(
    session: Session = Depends(get_session),
    user_id: UUID = Depends(get_current_user_id),
):
    """Mark all unread notifications as read."""
    count = notification_service.mark_all_as_read(session=session, user_id=user_id)
    return MarkAsReadResponse(success=True, count=count)


@router.patch("/{notification_id}/clicked", status_code=status.HTTP_200_OK, response_model=MarkAsReadResponse)
def mark_notification_as_clicked(
    notification_id: UUID,
    session: Session = Depends(get_session),
    user_id: UUID = Depends(get_current_user_id),
):
    """Mark a notification as clicked (also marks as read if not already)."""
    success = notification_service.mark_notification_as_clicked(
        session=session,
        user_id=user_id,
        notification_id=notification_id,
    )
    if not success:
        raise NotFoundError("Notificación no encontrada")
    return MarkAsReadResponse(success=True, count=1)


@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_notification(notification_id: UUID, session: Session = Depends(get_session), user_id: UUID = Depends(get_current_user_id)):
    """Soft delete a notification."""
    success = notification_service.delete_notification(session=session, user_id=user_id, notification_id=notification_id)
    if not success:
        raise NotFoundError("Notificación no encontrada")
