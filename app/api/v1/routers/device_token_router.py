from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlmodel import Session

from app.core.database import get_session
from app.core.security import get_current_user_id
from app.schemas.message import MessageResponse
from app.services import device_token_service as service
from app.schemas.device_token import DeviceTokenRegisterRequest, DeviceTokenResponse, DeviceTokenListResponse

router = APIRouter(prefix="/device-tokens", tags=["Device Tokens"])


@router.post("", status_code=status.HTTP_201_CREATED, response_model=DeviceTokenResponse, summary="Register device token", description="Register or update FCM device token for current user")
def register_device_token(data: DeviceTokenRegisterRequest, session: Session = Depends(get_session), user_id: UUID = Depends(get_current_user_id)):
    """Register device token for push notifications."""
    return service.register_device_token(session, user_id, data)


@router.get("", status_code=status.HTTP_200_OK, response_model=DeviceTokenListResponse, summary="Get user device tokens", description="Get all active device tokens for current user")
def get_device_tokens(session: Session = Depends(get_session), user_id: UUID = Depends(get_current_user_id)):
    """Get all device tokens for current user."""
    return service.get_user_device_tokens(session, user_id, active_only=True)


@router.delete("/{token}", status_code=status.HTTP_204_NO_CONTENT, summary="Unregister device token", description="Deactivate device token (soft delete)")
def unregister_device_token(token: str, session: Session = Depends(get_session), user_id: UUID = Depends(get_current_user_id)) -> None:
    """Unregister device token."""
    service.unregister_device_token(session, token, user_id)

@router.post("/logout", status_code=status.HTTP_200_OK, summary="Deactivate all user tokens", description="Deactivate all device tokens for current user (useful on logout)")
def logout_all_devices(session: Session = Depends(get_session), user_id: UUID = Depends(get_current_user_id)) -> MessageResponse:
    """Deactivate all device tokens for user."""
    count = service.deactivate_all_user_tokens(session, user_id)
    return MessageResponse(message=f"Deactivated {count} tokens")
