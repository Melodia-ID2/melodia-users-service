from uuid import UUID
from typing import Any, TypedDict
from sqlmodel import Session
from app.models.notification import NotificationType
from app.services import notification_service


class FilterReasons(TypedDict):
    user_disabled: int
    artist_muted: int
    no_tokens: int


class EventStats(TypedDict):
    notifications_created: int
    notifications_sent: int
    notifications_filtered: int
    filter_reasons: FilterReasons


def _init_stats() -> EventStats:
    return {
        "notifications_created": 0,
        "notifications_sent": 0,
        "notifications_filtered": 0,
        "filter_reasons": {"user_disabled": 0, "artist_muted": 0, "no_tokens": 0},
    }


def _map_reason(reason: str | None) -> str | None:
    if reason == "user_disabled_notification_type":
        return "user_disabled"
    if reason == "artist_muted":
        return "artist_muted"
    if reason == "no_device_tokens":
        return "no_tokens"
    return None


def process_notification_event(
    session: Session,
    event_type: NotificationType,
    title: str,
    body: str,
    target_user_ids: list[UUID],
    actor_id: UUID | None = None,
    image_url: str | None = None,
    metadata: dict[str, Any] | None = None
) -> EventStats:
    stats: EventStats = _init_stats()
    for user_id in target_user_ids:
        result = notification_service.send_notification_to_user(
            session=session,
            user_id=user_id,
            notification_type=event_type,
            title=title,
            body=body,
            data=metadata or {},
            image_url=image_url,
            actor_id=actor_id,
        )
        if result.get("reason"):
            stats["notifications_filtered"] += 1
            mapped = _map_reason(result.get("reason"))
            if mapped:
                stats["filter_reasons"][mapped] += 1
        else:
            stats["notifications_created"] += 1
            if result.get("sent"):
                stats["notifications_sent"] += 1
    return stats
