from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlmodel import Session

import app.services.admin_service as service
from app.core.database import get_session
from app.core.security import require_admin
from app.errors.error_responses import error_responses
from app.schemas.user import GetAllUserResponse, UserDetailedInfo, UserRoleUpdateResponse

router = APIRouter(prefix="/admin", tags=["Admin - User Management"])


@router.get("", response_model=GetAllUserResponse, status_code=status.HTTP_200_OK, responses=error_responses(401))
def get_all_users(
    session: Session = Depends(get_session),
    _: None = Depends(require_admin),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
):
    return service.get_all_users(session, page, page_size)


@router.get("/{user_id}", response_model=UserDetailedInfo, status_code=status.HTTP_200_OK, responses=error_responses(401, 404))
def get_user(
    user_id: UUID,
    session: Session = Depends(get_session),
    _: None = Depends(require_admin),
):
    return service.get_user(session, user_id)


@router.patch("/{user_id}/role", response_model=UserRoleUpdateResponse, status_code=status.HTTP_200_OK, responses=error_responses(401, 404))
async def update_user_role(
    user_id: UUID,
    session: Session = Depends(get_session),
    _: None = Depends(require_admin),
):
    return await service.update_user_role(session, user_id)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT, responses=error_responses(401, 404))
async def delete_user(
    user_id: UUID,
    session: Session = Depends(get_session),
    _: None = Depends(require_admin),
):
    return await service.delete_user(session, user_id)
