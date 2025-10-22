from uuid import UUID
from pydantic import EmailStr
from sqlmodel import Session, select

from app.models.usercredential import UserCredential


def get_primary_email_by_user_id(session: Session, user_id: UUID) -> EmailStr | None:
    primary_credential = session.exec(
        select(UserCredential.email)
        .where(UserCredential.user_id == user_id)
        .order_by(UserCredential.provider.desc())
    ).first()

    return primary_credential
