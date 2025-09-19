from uuid import UUID

from app.errors.exceptions import NotFoundError
from app.models.user import UserAccountStatus, UserProfile, UserRole
from sqlmodel import Session
import cloudinary.uploader

from app.schemas.user import UserDetailedInfo, UserProfileCreate, UserProfileResponse
from app.schemas.photo_profile import PhotoProfileResponse
import app.repositories.users_repository as repo

from app.errors.exceptions import UsernameTakenError, ProfileAlreadyExistsError

def get_all_users(session: Session) -> list[dict[str, str]]:
    users = repo.get_all_users(session)
    return [
        {"id": str(u[0]), "username": u[1], "email": u[2], "role": u[3], "status": u[4]} for u in users
    ]


def get_user(session: Session, user_id: UUID) -> UserDetailedInfo:
    user = repo.get_user_account_by_id(session, user_id)
    if not user:
        raise NotFoundError("User with id: {} not found".format(user_id))
    user_profile = repo.get_profile_by_id(session, user_id)
    return UserDetailedInfo(
        id=str(user.id),
        username=None if not user_profile else user_profile.username,
        email=user.email,
        role=user.role,
        status=user.status,
        full_name=None if not user_profile else user_profile.full_name,
        phone_number=None if not user_profile else user_profile.phone_number,
        address=None if not user_profile else user_profile.address,
        birthdate=None if not user_profile else user_profile.birthdate,
        last_login=user.last_login,
        created_at=user.created_at,
        profile_photo=None if not user_profile else user_profile.photo_profile,
    )


def create_user_profile(
    session: Session, user_id: UUID, profile_data: UserProfileCreate
) -> UserProfileResponse:
    existing_profile = repo.get_profile_by_id(session, user_id)
    if existing_profile:
        raise ProfileAlreadyExistsError("El perfil ya existe")
    if profile_data.username and profile_data.username.strip():
        existing_username = repo.get_profile_by_username(session, profile_data.username)
        if existing_username:
            raise UsernameTakenError("El nombre de usuario ya está en uso")
    new_profile = UserProfile(id=user_id, **profile_data.model_dump())
    new_profile = repo.create_user_profile(session, new_profile)
    return UserProfileResponse.model_validate(new_profile)


def update_user_role(session: Session, user_id: UUID) -> UserDetailedInfo:
    user = repo.get_user_account_by_id(session, user_id)
    if not user:
        raise NotFoundError("User with id: {} not found".format(user_id))
    user_profile = repo.get_profile_by_id(session, user_id)
    user.role = UserRole.ARTIST if user.role == UserRole.LISTENER else UserRole.LISTENER
    _ = repo.create_user_account(session, user)
    username= None if not user_profile else user_profile.username
    return UserDetailedInfo(
        id=str(user.id),
        username=username,
        email=user.email,
        role=user.role,
        status=user.status,
        phone_number=None if not user_profile else user_profile.phone_number,
        address=None if not user_profile else user_profile.address,
        last_login=user.last_login,
        created_at=user.created_at,
    )

def delete_user(session: Session, user_id: UUID):
    account = repo.get_user_account_by_id(session, user_id)
    if not account:
        raise NotFoundError("User with id: {} not found".format(user_id))
    _= repo.delete_user_account(session, account)
    return None


def update_photo_profile(session: Session,user_id: UUID, photo_file_bytes: bytes) -> PhotoProfileResponse:
    uploaded_url = cloudinary.uploader.upload(
            photo_file_bytes,
            folder="user-photo-profile",
            public_id=str(user_id),
            overwrite=True
        )["secure_url"]

    if not uploaded_url:
        raise FileUploadError("Error at upload photo profile")
    if not repo.update_photo_profile(session,user_id, uploaded_url):
        raise NotFoundError("User with id: {} not found".format(user_id))


    return PhotoProfileResponse(photo_profile=uploaded_url)