from typing import Any, Union
from uuid import UUID

import cloudinary.uploader
from sqlmodel import Session

import app.repositories.artist_repository as artists_repo
import app.repositories.users_repository as users_repo
from app.constants.notification_flags import NotificationPreferences
from app.errors.exceptions import FileUploadError, NotFoundError, ProfileAlreadyExistsError, UsernameTakenError, ValidationError
from app.models.useraccount import UserRole, UserStatus
from app.models.userprofile import UserProfile
from app.schemas.message import MessageResponse
from app.schemas.notifications import NotificationPreferencesResponse, NotificationPreferencesUpdate
from app.schemas.profile_photo import ProfilePhotoResponse
from app.schemas.user import (
    ArtistProfileResponse,
    FollowsListResponse,
    UserProfilePublic,
    UserProfileCreate,
    UserProfileResponse,
    UserProfileUpdate,
    UserSearchIndex,
)
from app.services.search_service import search_service


async def create_user_profile(session: Session, user_id: UUID, profile_data: UserProfileCreate) -> UserProfileResponse:
    existing_profile = users_repo.get_profile_by_id(session, user_id)
    if existing_profile:
        raise ProfileAlreadyExistsError("El perfil ya existe")

    existing_username = users_repo.get_profile_by_username(session, profile_data.username)
    if existing_username:
        raise UsernameTakenError("El nombre de usuario ya está en uso")
    
    new_profile = UserProfile(id=user_id, **profile_data.model_dump())
    new_profile = users_repo.create_user_profile(session, new_profile)
    
    user_account = users_repo.get_account_by_id(session, user_id)    
    if not user_account:
        raise NotFoundError("Cuenta de usuario no encontrada") # pragma: no cover # Defensive: user profile exists only if account exists (foreign key)
    
    search_data = UserSearchIndex(
        id=str(user_id),
        name=new_profile.username,
        role=user_account.role,
        image_url=new_profile.profile_photo,
        is_blocked=False
    )
    import asyncio
    asyncio.create_task(search_service.index_user(search_data))
    
    return UserProfileResponse.model_validate(new_profile)


async def update_profile_picture(session: Session, user_id: UUID, photo_file_bytes: bytes) -> ProfilePhotoResponse:
    uploaded_url = cloudinary.uploader.upload(photo_file_bytes, folder="user-photo-profile", public_id=str(user_id), overwrite=True)["secure_url"]
    if not uploaded_url:
        raise FileUploadError("Error al guardar la foto de perfil")

    user_profile = users_repo.update_profile_picture(session, user_id, uploaded_url)
    if not user_profile:
        raise NotFoundError("Usuario con id: {} no encontrado".format(user_id)) # pragma: no cover # Defensive: already checked in JWT

    user_account = users_repo.get_account_by_id(session, user_id)    
    if not user_account:
        raise NotFoundError("Cuenta de usuario no encontrada") # pragma: no cover # Defensive: user profile exists only if account exists (foreign key)

    search_data = UserSearchIndex(
        id=str(user_id),
        name=user_profile.username,
        role=user_account.role,
        image_url=user_profile.profile_photo,
        is_blocked=user_account.status == UserStatus.BLOCKED
    )
    import asyncio
    asyncio.create_task(search_service.index_user(search_data))

    return ProfilePhotoResponse(profile_photo=uploaded_url)


def get_me(session: Session, user_id: UUID) -> Union[UserProfileResponse, ArtistProfileResponse]:
    profile = users_repo.get_profile_by_id(session, user_id)
    if not profile:
        raise NotFoundError("Perfil no encontrado") # pragma: no cover # Defensive: already checked in JWT

    user_account = users_repo.get_account_by_id(session, user_id)
    if not user_account:
        raise NotFoundError("Cuenta de usuario no encontrada") # pragma: no cover # Defensive: user profile exists only if account exists (foreign key)

    response_data: dict[str, Any] = {
        "id": profile.id,
        "username": profile.username,
        "full_name": profile.full_name,
        "birthdate": profile.birthdate,
        "gender": profile.gender,
        "phone_number": profile.phone_number,
        "address": profile.address,
        "profile_photo": profile.profile_photo,
        "bio": profile.bio,
        "followers_count": profile.followers_count,
        "following_count": profile.following_count,
        "preferences": user_account.preferences,
    }

    if user_account.role == UserRole.ARTIST:
        photos = artists_repo.get_artist_photos(session, user_id)
        links = artists_repo.get_artist_links(session, user_id)
        response_data = response_data | {"photos": [photo.url for photo in photos], "links": [link.url for link in links]}
        return ArtistProfileResponse(**response_data)
    else:
        return UserProfileResponse(**response_data)



async def update_me(session: Session, user_id: UUID, data: UserProfileUpdate) -> UserProfileResponse:
    profile = users_repo.get_user_profile_by_user_id(session, user_id)
    if not profile:
        raise NotFoundError("Perfil no encontrado") # pragma: no cover # Defensive: already checked in JWT

    if data.username and data.username.strip() and data.username != profile.username:
        existing_username = users_repo.get_profile_by_username(session, data.username)
        if existing_username:
            raise UsernameTakenError("El nombre de usuario ya está en uso")

    update_data = data.model_dump(exclude_unset=True)
    updated_profile = users_repo.update_user_profile(session, user_id, update_data)
    if not updated_profile:
        raise NotFoundError("Perfil no encontrado") # pragma: no cover # Defensive: already checked above

    user_account = users_repo.get_account_by_id(session, user_id)
    if not user_account:
        raise NotFoundError("Cuenta de usuario no encontrada") # pragma: no cover # Defensive: user profile exists only if account exists (foreign key)

    search_data = UserSearchIndex(
        id=str(user_id),
        name=updated_profile.username,
        role=user_account.role,
        image_url=updated_profile.profile_photo,
        is_blocked=user_account.status == UserStatus.BLOCKED
    )
    import asyncio
    asyncio.create_task(search_service.index_user(search_data))

    return UserProfileResponse(
        id=updated_profile.id,
        username=updated_profile.username,
        full_name=updated_profile.full_name,
        birthdate=updated_profile.birthdate,
        gender=updated_profile.gender,
        phone_number=updated_profile.phone_number,
        address=updated_profile.address,
        profile_photo=updated_profile.profile_photo,
        bio=updated_profile.bio,
        followers_count=updated_profile.followers_count,
        following_count=updated_profile.following_count,
        preferences=user_account.preferences,
    )


def get_public_profile(session: Session, user_id: UUID, current_user_id: UUID) -> UserProfilePublic:
    account = users_repo.get_account_by_id(session, user_id)
    if not account:
        raise NotFoundError("Cuenta de usuario no encontrada")

    profile = users_repo.get_profile_by_id(session, user_id)
    if not profile:
        raise NotFoundError("Perfil de usuario no encontrado")

    photos_list: list[str] = []
    links_list: list[str] = []
    if account.role == UserRole.ARTIST:
        photos_list = [photo.url for photo in artists_repo.get_artist_photos(session, user_id)]
        links_list = [link.url for link in artists_repo.get_artist_links(session, user_id)]

    return UserProfilePublic(
        id=str(user_id),
        role=account.role,
        username=profile.username,
        profile_photo=profile.profile_photo,
        bio=profile.bio,
        followers_count=profile.followers_count,
        following_count=profile.following_count,
        is_following=users_repo.is_following(session, current_user_id, user_id),
        photos=photos_list,
        links=links_list,
    )


def follow_user(session: Session, current_user_id: UUID, user_id: UUID) -> MessageResponse:
    if current_user_id == user_id:
        raise ValidationError("No puedes seguirte a ti mismo.")

    followed = users_repo.get_profile_by_id(session, user_id)
    if not followed:
        raise NotFoundError("Usuario a seguir no encontrado")

    is_now_following = users_repo.toggle_follow(session, current_user_id, user_id)
    if is_now_following:
        return MessageResponse(message=f"Ahora sigues a {followed.username}")
    else:
        return MessageResponse(message=f"Dejaste de seguir a {followed.username}")


def get_followers(session: Session, user_id: UUID, current_user_id: UUID) -> FollowsListResponse:
    followers = users_repo.get_followers(session, user_id, current_user_id)
    return FollowsListResponse(follows=followers)


def get_following(session: Session, user_id: UUID, current_user_id: UUID) -> FollowsListResponse:
    following = users_repo.get_following(session, user_id, current_user_id)
    return FollowsListResponse(follows=following)

def change_history_preferences(session: Session, user_id: UUID) -> MessageResponse:
    account = users_repo.change_history_preferences(session, user_id)
    if not account:
        raise NotFoundError("Cuenta de usuario no encontrada") # pragma: no cover # Defensive: already checked in JWT
    status = "activado" if account.preferences & 0b1 else "desactivado"
    return MessageResponse(message=f"Historial {status} exitosamente.")


def get_notification_preferences(session: Session, user_id: UUID) -> NotificationPreferencesResponse:
    prefs_value = users_repo.get_user_preferences(session, user_id)
    if prefs_value is None:
        raise NotFoundError("Cuenta de usuario no encontrada")  # pragma: no cover # Defensive: already checked in JWT

    prefs = NotificationPreferences(prefs_value)
    return NotificationPreferencesResponse(**prefs.as_dict())


def update_notification_preferences(session: Session, user_id: UUID, data: NotificationPreferencesUpdate) -> NotificationPreferencesResponse:
    new_prefs_value = NotificationPreferences.from_dict(data.model_dump())
    account = users_repo.update_notification_preferences(session, user_id, new_prefs_value)
    if not account:
        raise NotFoundError("Cuenta de usuario no encontrada")  # pragma: no cover

    updated_prefs = NotificationPreferences(account.preferences)
    return NotificationPreferencesResponse(**updated_prefs.as_dict())
