from uuid import UUID
from app.errors.error_responses import error_responses
from fastapi import APIRouter, Depends, status, UploadFile, File
from app.schemas.user import GetAllUserResponse, UserDetailedInfo, UserProfileCreate, UserRoleUpdateResponse
from sqlmodel import Session
from app.core.database import get_session
from app.core.security import get_current_user_id, require_admin
import app.controllers.users_controller as controller
from app.schemas.photo_profile import PhotoProfileResponse

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/", response_model=GetAllUserResponse, status_code=status.HTTP_200_OK, responses= error_responses(401))
def get_all_users(
    session: Session = Depends(get_session), _: None = Depends(require_admin)
):
    return controller.get_all_users(session)


@router.get("/{user_id}", response_model=UserDetailedInfo, status_code=status.HTTP_200_OK, responses= error_responses(401, 404))
def get_user(
    user_id: UUID,
    session: Session = Depends(get_session),
    _: None = Depends(require_admin),
):
    return controller.get_user(session, user_id)


@router.patch("/{user_id}/role", response_model=UserRoleUpdateResponse, status_code=status.HTTP_200_OK, responses= error_responses(401, 404))
def update_user_role(
    user_id: UUID,
    session: Session = Depends(get_session),
    _: None = Depends(require_admin),
):
    return controller.update_user_role(session, user_id)


@router.post("/profile", status_code=status.HTTP_201_CREATED)
def create_user_profile(
    profile_data: UserProfileCreate,
    session: Session = Depends(get_session),
    user_id: UUID = Depends(get_current_user_id),
):
    return controller.create_user_profile(session, user_id, profile_data)

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT, responses= error_responses(401, 404))
def delete_user(
    user_id: UUID,
    session: Session = Depends(get_session),
    _: None = Depends(require_admin),
):
    return controller.delete_user(session, user_id)


@router.post("/photo-profile", response_model=PhotoProfileResponse)
async def update_photo_profile(
    file: UploadFile = File(...), 
    current_user_id: UUID = Depends(get_current_user_id),
    session: Session = Depends(get_session),
):
    return await controller.update_photo_profile(session,current_user_id, file)
