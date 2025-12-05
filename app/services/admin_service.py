from uuid import UUID

import cloudinary.uploader
from sqlmodel import Session

import app.repositories.admin_repository as admin_repo
import app.repositories.users_repository as users_repo
from app.errors.exceptions import NotFoundError
from app.models.useraccount import UserRole, UserStatus
from app.repositories import credentials_repository as credentials_repo
from app.schemas.user import (
    GetAllUserResponse,
    UserDetailedInfo,
    UserRoleUpdateResponse,
    UserSearchIndex,
)
from app.services.search_service import search_service


def get_all_users(
    session: Session,
    page: int,
    page_size: int,
    role: UserRole | None = None,
    sort_by: str = "created_at",
    sort_order: str = "asc",
) -> GetAllUserResponse:
    users, total = admin_repo.get_all_users(session, page, page_size, role, sort_by, sort_order)
    return GetAllUserResponse(
        users=[{
            "id": str(u.id),
            "username": u.username,
            "email": u.email or "",
            "role": u.role,
            "status": u.status,
            "profile_photo": u.profile_photo,
        } for u in users],
        total=total or 0,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size if total else 0,
    )


def get_user(session: Session, user_id: UUID) -> UserDetailedInfo:
    user_account = users_repo.get_account_by_id(session, user_id)
    if not user_account:
        raise NotFoundError(f"Cuenta de usuario con id: {user_id} no encontrada")

    user_profile = users_repo.get_profile_by_id(session, user_id)
    if not user_profile:
        raise NotFoundError(f"Perfil de usuario con id: {user_id} no encontrado")

    return UserDetailedInfo(
        id=str(user_account.id),
        username=user_profile.username,
        email=credentials_repo.get_primary_email_by_user_id(session, user_id) or "",
        role=user_account.role,
        status=user_account.status,
        full_name=user_profile.full_name,
        phone_number=user_profile.phone_number,
        address=user_profile.address,
        country=user_account.country,
        birthdate=user_profile.birthdate,
        last_login=user_account.last_login,
        created_at=user_account.created_at,
        profile_photo=user_profile.profile_photo,
    )


def update_user_role(session: Session, user_id: UUID) -> UserRoleUpdateResponse:
    user = users_repo.get_account_by_id(session, user_id)
    if not user:
        raise NotFoundError(f"Cuenta de usuario con id: {user_id} no encontrada")
    
    search_service.delete_user(user.role, user_id)
    user.role = UserRole.ARTIST if user.role == UserRole.LISTENER else UserRole.LISTENER
    user_account = users_repo.create_user_account(session, user)

    user_profile = users_repo.get_profile_by_id(session, user_id)
    if user_profile:
        search_data = UserSearchIndex(
            id=str(user_id),
            name=user_profile.username,
            role=user_account.role,
            image_url=user_profile.profile_photo,
            is_blocked=user_account.status == UserStatus.BLOCKED
        )
        search_service.index_user(search_data)


    return UserRoleUpdateResponse(
        id=str(user.id),
        role=user.role,
    )


def delete_user(session: Session, user_id: UUID) -> None:
    account = users_repo.get_account_by_id(session, user_id)
    if not account:
        raise NotFoundError("Usuario con id: {} no encontrado".format(user_id))
        
    user_profile = users_repo.get_profile_by_id(session, user_id)
    if user_profile and user_profile.profile_photo:
        cloudinary.uploader.destroy(public_id=f"user-photo-profile/{user_id}")

    search_service.delete_user(account.role, user_id)

    admin_repo.delete_user_account(session, account)
    return None
