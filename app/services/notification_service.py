from datetime import datetime, timezone
from uuid import UUID
from typing import Any
from sqlmodel import Session
from app.models.notification import Notification, NotificationType
from app.repositories import notification_repository as notif_repo
from app.repositories import device_token_repository as token_repo
from app.repositories import users_repository as user_repo
from app.repositories import muted_artists_repository as muted_repo
from app.services.fcm_service import fcm_service
from app.constants.notification_flags import (
    BIT_NOTIFICATIONS_NEW_RELEASES,
    BIT_NOTIFICATIONS_FOLLOW_ACTIVITY,
    BIT_NOTIFICATIONS_SHARED_CONTENT,
    BIT_NOTIFICATIONS_NEW_FOLLOWERS,
    BIT_NOTIFICATIONS_PLAYLIST_LIKES,
    NotificationPreferences
)


NOTIFICATION_TYPE_TO_FLAG = {
    NotificationType.NEW_RELEASE: BIT_NOTIFICATIONS_NEW_RELEASES,
    NotificationType.PLAYLIST_PUBLISHED: BIT_NOTIFICATIONS_FOLLOW_ACTIVITY,
    NotificationType.CONTENT_SHARED: BIT_NOTIFICATIONS_SHARED_CONTENT,
    NotificationType.NEW_FOLLOWER: BIT_NOTIFICATIONS_NEW_FOLLOWERS,
    NotificationType.PLAYLIST_LIKED: BIT_NOTIFICATIONS_PLAYLIST_LIKES,
}


def build_deep_link(notification_type: NotificationType, metadata: dict[str, Any]) -> str:
    base = "com.melodia.is2://"
    
    match notification_type:
        case NotificationType.NEW_RELEASE:
            collection_id = metadata.get("collection_id") or metadata.get("collectionId")
            return f"{base}collection/{collection_id}" if collection_id else f"{base}notifications"

        case NotificationType.PLAYLIST_PUBLISHED | NotificationType.PLAYLIST_LIKED:
            playlist_id = metadata.get("playlist_id") or metadata.get("playlistId")
            return f"{base}playlist/{playlist_id}" if playlist_id else f"{base}notifications"

        case NotificationType.NEW_FOLLOWER:
            follower_id = metadata.get("follower_id") or metadata.get("followerId")
            return f"{base}user/{follower_id}" if follower_id else f"{base}notifications"

        case NotificationType.CONTENT_SHARED:
            content_type = (metadata.get("content_type") or metadata.get("contentType") or "").lower()
            if content_type == "song":
                collection_id = metadata.get("collection_id") or metadata.get("collectionId")
                return f"{base}collection/{collection_id}" if collection_id else f"{base}notifications"
            if content_type == "playlist":
                playlist_id = metadata.get("playlist_id") or metadata.get("playlistId")
                return f"{base}playlist/{playlist_id}" if playlist_id else f"{base}notifications"
            return f"{base}notifications"

        case _:
            return f"{base}notifications"


def send_notification_to_user(
    session: Session,
    user_id: UUID,
    notification_type: NotificationType,
    title: str,
    body: str,
    data: dict[str, Any] | None = None,
    image_url: str | None = None,
    actor_id: UUID | None = None
 ) -> dict[str, Any]:
    user_account = user_repo.get_account_by_id(session, user_id)
    if not user_account:
        return {"sent": False, "reason": "user_not_found"}
    
    preferences = NotificationPreferences(user_account.preferences)
    required_flag = NOTIFICATION_TYPE_TO_FLAG.get(notification_type)
    
    should_send = True
    skip_reason = None
    
    if required_flag and not preferences.has(required_flag):
        should_send = False
        skip_reason = "user_disabled_notification_type"
    
    if should_send and notification_type == NotificationType.NEW_RELEASE and actor_id:
        is_muted = muted_repo.is_artist_muted(session, user_id, actor_id)
        if is_muted:
            should_send = False
            skip_reason = "artist_muted"
    
    device_tokens = token_repo.get_user_device_tokens(session, user_id, active_only=True)
    if should_send and not device_tokens:
        should_send = False
        skip_reason = "no_device_tokens"
    
    success_count = 0
    failed_tokens: list[str] = []
    sent_at = None

    deep_link = build_deep_link(notification_type, data or {})
    enriched_data: dict[str, Any] = {
        **(data or {}),
        "deep_link": deep_link,
        "notification_type": notification_type.value,
    }
    
    if should_send and device_tokens:
        tokens_list = [dt.device_token for dt in device_tokens]
        
        fcm_data = {k: str(v) for k, v in enriched_data.items()}
        
        result = fcm_service.send_multicast(
            tokens=tokens_list,
            title=title,
            body=body,
            data=fcm_data,
            image_url=image_url
        )
        
        success_count = result["success_count"]
        failed_tokens = result["failed_tokens"]
        
        for failed_token in failed_tokens:
            token_repo.deactivate_device_token(session, failed_token)
        
        if success_count > 0:
            sent_at = datetime.now(timezone.utc)
        
        notif_repo.create_notification(
            session=session,
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            body=body,
            data=enriched_data,
            image_url=image_url,
            sent_at=sent_at
        )
    
    return {
        "sent": success_count > 0,
        "success_count": success_count,
        "failed_tokens": failed_tokens,
        "reason": skip_reason if not should_send else None
    }


def send_notification_to_users(
    session: Session,
    user_ids: list[UUID],
    notification_type: NotificationType,
    title: str,
    body: str,
    data: dict[str, Any] | None = None,
    image_url: str | None = None,
    actor_id: UUID | None = None
) -> dict[str, Any]:
    results: dict[str, Any] = {
        "sent_count": 0,
        "filtered_count": 0,
        "filter_reasons": {
            "user_disabled": 0,
            "artist_muted": 0,
            "no_tokens": 0
        }
    }
    
    for user_id in user_ids:
        result = send_notification_to_user(
            session=session,
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            body=body,
            data=data,
            image_url=image_url,
            actor_id=actor_id
        )
        
        if result["sent"]:
            results["sent_count"] += 1
        else:
            results["filtered_count"] += 1
            reason = result.get("reason", "unknown")
            if reason == "user_disabled_notification_type":
                results["filter_reasons"]["user_disabled"] += 1
            elif reason == "artist_muted":
                results["filter_reasons"]["artist_muted"] += 1
            elif reason == "no_device_tokens":
                results["filter_reasons"]["no_tokens"] += 1
    
    return results


def get_user_notifications(
    session: Session,
    user_id: UUID,
    limit: int = 20,
    offset: int = 0,
    unread_only: bool = False
):
    return notif_repo.get_user_notifications(
        session=session,
        user_id=user_id,
        limit=limit,
        offset=offset,
        unread_only=unread_only,
    )


def get_unread_count(session: Session, user_id: UUID) -> int:
    return notif_repo.get_unread_count(session=session, user_id=user_id)


def mark_notification_as_read(session: Session, user_id: UUID, notification_id: UUID) -> bool:
    notification = session.get(Notification, notification_id)
    if not notification or notification.user_id != user_id:
        return False
    return notif_repo.mark_as_read(session=session, notification_id=notification_id)


def mark_all_as_read(session: Session, user_id: UUID) -> int:
    return notif_repo.mark_all_as_read(session=session, user_id=user_id)


def mark_notification_as_clicked(session: Session, user_id: UUID, notification_id: UUID) -> bool:
    notification = session.get(Notification, notification_id)
    if not notification or notification.user_id != user_id:
        return False
    return notif_repo.mark_as_clicked(session=session, notification_id=notification_id)


def delete_notification(session: Session, user_id: UUID, notification_id: UUID) -> bool:
    return notif_repo.delete_notification(session=session, notification_id=notification_id, user_id=user_id)
