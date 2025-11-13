from uuid import UUID
from sqlmodel import Session
from app.errors.exceptions import NotFoundError, ValidationError
from app.repositories import device_token_repository as repo
from app.schemas.device_token import DeviceTokenRegisterRequest, DeviceTokenResponse, DeviceTokenListResponse


def register_device_token(session: Session, user_id: UUID, data: DeviceTokenRegisterRequest) -> DeviceTokenResponse:
    token = repo.create_device_token(
        session=session,
        user_id=user_id,
        device_token=data.device_token,
        platform=data.platform
    )
    return DeviceTokenResponse.model_validate(token)


def get_user_device_tokens(session: Session, user_id: UUID, active_only: bool = True) -> DeviceTokenListResponse:
    tokens = repo.get_user_device_tokens(session, user_id, active_only)
    return DeviceTokenListResponse(
        tokens=[DeviceTokenResponse.model_validate(t) for t in tokens],
        total=len(tokens)
    )


def unregister_device_token(session: Session, token: str, user_id: UUID) -> None:
    device_token = repo.get_device_token_by_token(session, token)
    if not device_token:
        raise NotFoundError("No se encontró el token de dispositivo.")
    if device_token.user_id != user_id:
        raise ValidationError("No tiene permiso para eliminar este token de dispositivo.")
    
    repo.deactivate_device_token(session, token)


def delete_device_token(session: Session, token: str) -> bool:
    return repo.delete_device_token(session, token)


def deactivate_all_user_tokens(session: Session, user_id: UUID) -> int:
    return repo.deactivate_user_tokens(session, user_id)