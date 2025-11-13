from datetime import datetime, timezone
from typing import Any
from uuid import UUID
from sqlmodel import Session, select, desc, func
from app.models.notification import Notification, NotificationType


def create_notification(
    session: Session,
    user_id: UUID,
    notification_type: NotificationType,
    title: str,
    body: str,
    data: dict[str, Any] | None = None,
    image_url: str | None = None,
    sent_at: datetime | None = None
) -> Notification:
    notification = Notification(
        user_id=user_id,
        type=notification_type,
        title=title,
        body=body,
        data=data or {},
        image_url=image_url,
        sent_at=sent_at
    )
    session.add(notification)
    session.commit()
    session.refresh(notification)
    return notification


def get_user_notifications(
    session: Session,
    user_id: UUID,
    limit: int = 20,
    offset: int = 0,
    unread_only: bool = False
) -> tuple[list[Notification], int]:
    query = select(Notification).where(
        Notification.user_id == user_id,
        Notification.deleted_at == None
    )
    
    if unread_only:
        query = query.where(Notification.read_at == None)
    
    count_query = select(func.count()).select_from(Notification).where(
        Notification.user_id == user_id,
        Notification.deleted_at == None
    )
    if unread_only:
        count_query = count_query.where(Notification.read_at == None)
    
    total = session.scalar(count_query) or 0
    
    query = query.order_by(desc(Notification.created_at)).limit(limit).offset(offset)
    notifications = list(session.exec(query).all())
    
    return notifications, total


def mark_as_read(session: Session, notification_id: UUID) -> bool:
    notification = session.get(Notification, notification_id)
    if not notification:
        return False
    
    notification.read_at = datetime.now(timezone.utc)
    session.add(notification)
    session.commit()
    return True


def mark_as_clicked(session: Session, notification_id: UUID) -> bool:
    notification = session.get(Notification, notification_id)
    if not notification:
        return False
    
    notification.clicked_at = datetime.now(timezone.utc)
    if not notification.read_at:
        notification.read_at = datetime.now(timezone.utc)
    
    session.add(notification)
    session.commit()
    return True


def mark_all_as_read(session: Session, user_id: UUID) -> int:
    notifications = session.exec(
        select(Notification)
        .where(Notification.user_id == user_id)
        .where(Notification.read_at == None)
        .where(Notification.deleted_at == None)
    ).all()
    
    count = 0
    now = datetime.now(timezone.utc)
    for notification in notifications:
        notification.read_at = now
        session.add(notification)
        count += 1
    
    if count > 0:
        session.commit()
    
    return count


def delete_notification(session: Session, notification_id: UUID, user_id: UUID) -> bool:
    notification = session.get(Notification, notification_id)
    if not notification or notification.user_id != user_id or notification.deleted_at:
        return False
    
    notification.deleted_at = datetime.now(timezone.utc)
    session.add(notification)
    session.commit()
    return True


def get_unread_count(session: Session, user_id: UUID) -> int:
    query = select(func.count()).select_from(Notification).where(
        Notification.user_id == user_id,
        Notification.read_at == None,
        Notification.deleted_at == None
    )
    return session.exec(query).one()
