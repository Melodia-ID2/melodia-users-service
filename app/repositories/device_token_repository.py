from datetime import datetime, timezone
from uuid import UUID
from sqlmodel import Session, select
from app.models.devicetoken import DeviceToken


def get_user_device_tokens(session: Session, user_id: UUID, active_only: bool = True) -> list[DeviceToken]:
    query = select(DeviceToken).where(DeviceToken.user_id == user_id)
    if active_only:
        query = query.where(DeviceToken.is_active == True)
    return list(session.exec(query).all())


def get_device_token_by_token(session: Session, token: str) -> DeviceToken | None:
    return session.exec(
        select(DeviceToken).where(DeviceToken.device_token == token)
    ).first()


def create_device_token(
    session: Session, 
    user_id: UUID, 
    device_token: str, 
    platform: str | None = None
) -> DeviceToken:
    existing = get_device_token_by_token(session, device_token)
    if existing:
        existing.user_id = user_id
        existing.platform = platform
        existing.is_active = True
        existing.updated_at = datetime.now(timezone.utc)
        session.add(existing)
        session.commit()
        session.refresh(existing)
        return existing
    
    new_token = DeviceToken(
        user_id=user_id,
        device_token=device_token,
        platform=platform,
        is_active=True
    )
    session.add(new_token)
    session.commit()
    session.refresh(new_token)
    return new_token


def deactivate_device_token(session: Session, token: str) -> bool:
    device_token = get_device_token_by_token(session, token)
    if not device_token:
        return False
    
    device_token.is_active = False
    device_token.updated_at = datetime.now(timezone.utc)
    session.add(device_token)
    session.commit()
    return True


def delete_device_token(session: Session, token: str) -> bool:
    device_token = get_device_token_by_token(session, token)
    if not device_token:
        return False
    
    session.delete(device_token)
    session.commit()
    return True


def deactivate_user_tokens(session: Session, user_id: UUID) -> int:
    tokens = get_user_device_tokens(session, user_id, active_only=True)
    count = 0
    for token in tokens:
        token.is_active = False
        token.updated_at = datetime.now(timezone.utc)
        session.add(token)
        count += 1
    
    if count > 0:
        session.commit()
    
    return count
