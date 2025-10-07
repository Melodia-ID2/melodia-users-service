from uuid import UUID
from app.errors.error_responses import error_responses
from fastapi import APIRouter, Depends, Query, status, UploadFile, File
from app.schemas.user import GetAllUserResponse, UserDetailedInfo, UserProfileCreate, UserProfileResponse, UserProfileUpdate, UserRoleUpdateResponse, SearchUsersResponse
from sqlmodel import Session
from app.core.database import get_session
from app.core.security import get_current_user_id, require_admin
import app.controllers.users_controller as controller
from app.schemas.photo_profile import PhotoProfileResponse
from app.api.v1.routers.admin_router import router as admin_router

router = APIRouter(prefix="/users", tags=["users"])

router.include_router(admin_router)

@router.get("/me", response_model=UserProfileResponse)
def get_me(
    session: Session = Depends(get_session),
    user_id: UUID = Depends(get_current_user_id),
):
    return controller.get_me(session, user_id)


@router.put("/me", response_model=UserProfileResponse)
def update_me(
    data: UserProfileUpdate,
    session: Session = Depends(get_session),
    user_id: UUID = Depends(get_current_user_id),
):
    return controller.update_me(session, user_id, data)


@router.get("/search", response_model=SearchUsersResponse, status_code=status.HTTP_200_OK)
def search_users(
    query: str = Query(..., min_length=1),
    role: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: Session = Depends(get_session),
):
    return controller.search_users(session, query, role, page, page_size)


@router.post("/profile", status_code=status.HTTP_201_CREATED)
def create_user_profile(
    profile_data: UserProfileCreate,
    session: Session = Depends(get_session),
    user_id: UUID = Depends(get_current_user_id),
):
    return controller.create_user_profile(session, user_id, profile_data)


@router.post("/photo-profile", response_model=PhotoProfileResponse)
async def update_photo_profile(
    file: UploadFile = File(...), 
    current_user_id: UUID = Depends(get_current_user_id),
    session: Session = Depends(get_session),
):
    return await controller.update_photo_profile(session,current_user_id, file)


