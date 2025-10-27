import time
from typing import Any, List, Union
from uuid import UUID, uuid4

import cloudinary.uploader
from pydantic import AnyUrl
from pydantic import ValidationError as PydanticValidationError
from sqlmodel import Session

import app.repositories.users_repository as repo
from app.errors.exceptions import FileUploadError, NotFoundError, ProfileAlreadyExistsError, UsernameTakenError, ValidationError
from app.models.useraccount import UserRole, UserStatus
from app.models.userprofile import UserProfile
from app.repositories import credentials_repository as credentials_repo
from app.schemas.artist import SocialLinksUpdateRequest
from app.schemas.message import MessageResponse
from app.schemas.profile_photo import ProfilePhotoResponse
from app.schemas.user import (
    ArtistProfileResponse,
    FollowsListResponse,
    GetAllUserResponse,
    UserProfilePublic,
    UserDetailedInfo,
    UserProfileCreate,
    UserProfileResponse,
    UserProfileUpdate,
    UserRoleUpdateResponse,
    UserSearchIndex,
)
from app.services.search_service import search_service


def get_all_users(session: Session, page: int, page_size: int) -> GetAllUserResponse:
    users, total = repo.get_all_users(session, page, page_size)
    return GetAllUserResponse(
        users=[{"id": str(u.id), "username": u.username, "email": u.email or "", "role": u.role, "status": u.status} for u in users],
        total=total or 0,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size if total else 0,
    )


def get_user(session: Session, user_id: UUID) -> UserDetailedInfo:
    user_account = repo.get_account_by_id(session, user_id)
    if not user_account:
        raise NotFoundError("Usuario con id: {} no encontrado".format(user_id))

    user_profile = repo.get_profile_by_id(session, user_id)
    if not user_profile:
        raise NotFoundError("Perfil de usuario con id: {} no encontrado".format(user_id))

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


async def create_user_profile(session: Session, user_id: UUID, profile_data: UserProfileCreate) -> UserProfileResponse:
    existing_profile = repo.get_profile_by_id(session, user_id)
    if existing_profile:
        raise ProfileAlreadyExistsError("El perfil ya existe")

    existing_username = repo.get_profile_by_username(session, profile_data.username)
    if existing_username:
        raise UsernameTakenError("El nombre de usuario ya está en uso")
    
    new_profile = UserProfile(id=user_id, **profile_data.model_dump())
    new_profile = repo.create_user_profile(session, new_profile)
    
    user_account = repo.get_account_by_id(session, user_id)    
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


async def update_user_role(session: Session, user_id: UUID) -> UserRoleUpdateResponse:
    user = repo.get_account_by_id(session, user_id)
    if not user:
        raise NotFoundError("Usuario con id: {} no encontrado".format(user_id))
    
    import asyncio
    asyncio.create_task(search_service.delete_user(user.role, user_id))
    user.role = UserRole.ARTIST if user.role == UserRole.LISTENER else UserRole.LISTENER
    user_account = repo.create_user_account(session, user)

    user_profile = repo.get_profile_by_id(session, user_id)
    if user_profile:
        search_data = UserSearchIndex(
            id=str(user_id),
            name=user_profile.username,
            role=user_account.role,
            image_url=user_profile.profile_photo,
            is_blocked=user_account.status == UserStatus.BLOCKED
        )
        asyncio.create_task(search_service.index_user(search_data))


    return UserRoleUpdateResponse(
        id=str(user.id),
        role=user.role,
    )


async def delete_user(session: Session, user_id: UUID) -> None:
    account = repo.get_account_by_id(session, user_id)
    if not account:
        raise NotFoundError("Usuario con id: {} no encontrado".format(user_id))
        
    user_profile = repo.get_profile_by_id(session, user_id)
    if user_profile and user_profile.profile_photo:
        cloudinary.uploader.destroy(public_id=f"user-photo-profile/{user_id}")

    import asyncio
    asyncio.create_task(search_service.delete_user(account.role, user_id))
    
    repo.delete_user_account(session, account)
    return None


async def update_profile_picture(session: Session, user_id: UUID, photo_file_bytes: bytes) -> ProfilePhotoResponse:
    uploaded_url = cloudinary.uploader.upload(photo_file_bytes, folder="user-photo-profile", public_id=str(user_id), overwrite=True)["secure_url"]
    if not uploaded_url:
        raise FileUploadError("Error al guardar la foto de perfil")

    user_profile = repo.update_profile_picture(session, user_id, uploaded_url)
    if not user_profile:
        raise NotFoundError("Usuario con id: {} no encontrado".format(user_id)) # pragma: no cover # Defensive: already checked in JWT

    user_account = repo.get_account_by_id(session, user_id)    
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
    profile = repo.get_profile_by_id(session, user_id)
    if not profile:
        raise NotFoundError("Perfil no encontrado")

    user_account = repo.get_account_by_id(session, user_id)
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
    }

    if user_account.role == UserRole.ARTIST:
        photos = repo.get_artist_photos(session, user_id)
        links = repo.get_artist_links(session, user_id)
        response_data = response_data | {"photos": [photo.url for photo in photos], "links": [link.url for link in links]}
        return ArtistProfileResponse(**response_data)
    else:
        return UserProfileResponse(**response_data)



async def update_me(session: Session, user_id: UUID, data: UserProfileUpdate) -> UserProfileResponse:
    profile = repo.get_user_profile_by_user_id(session, user_id)
    if not profile:
        raise NotFoundError("Perfil no encontrado") # pragma: no cover # Defensive: already checked in JWT

    if data.username and data.username.strip() and data.username != profile.username:
        existing_username = repo.get_profile_by_username(session, data.username)
        if existing_username:
            raise UsernameTakenError("El nombre de usuario ya está en uso")

    update_data = data.model_dump(exclude_unset=True)
    updated_profile = repo.update_user_profile(session, user_id, update_data)
    if not updated_profile:
        raise NotFoundError("Perfil no encontrado") # pragma: no cover # Defensive: already checked above

    user_account = repo.get_account_by_id(session, user_id)
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
    )


def get_public_profile(session: Session, user_id: UUID, current_user_id: UUID) -> UserProfilePublic:
    account = repo.get_account_by_id(session, user_id)
    if not account:
        raise NotFoundError("Cuenta de usuario no encontrada")

    profile = repo.get_profile_by_id(session, user_id)
    if not profile:
        raise NotFoundError("Perfil de usuario no encontrado")

    photos_list: list[str] = []
    links_list: list[str] = []
    if account.role == UserRole.ARTIST:
        photos_list = [photo.url for photo in repo.get_artist_photos(session, user_id)]
        links_list = [link.url for link in repo.get_artist_links(session, user_id)]

    return UserProfilePublic(
        id=str(user_id),
        role=account.role,
        username=profile.username,
        profile_photo=profile.profile_photo,
        bio=profile.bio,
        followers_count=profile.followers_count,
        following_count=profile.following_count,
        is_following=repo.is_following(session, current_user_id, user_id),
        photos=photos_list,
        links=links_list,
    )


def update_artist_social_links(session: Session, user_id: UUID, data: SocialLinksUpdateRequest) -> None:
    account = repo.get_account_by_id(session, user_id)
    if not account or account.role != UserRole.ARTIST:
        raise NotFoundError("Solo los artistas pueden modificar sus redes sociales")

    for url in data.links:
        if url.strip():  # Solo validar URLs no vacías
            try:
                AnyUrl(url=url)
            except PydanticValidationError:
                raise ValidationError(f"El link '{url}' no es una URL válida.")

    valid_links = [url.strip() for url in data.links if url.strip()]

    repo.update_artist_social_links(session, user_id, valid_links)

    return None


def add_artist_photo(session: Session, user_id: UUID, photo_file_bytes: bytes) -> dict[str, str | int]:
    """
    Agrega una foto al perfil del artista.
    Máximo 5 fotos permitidas.
    """
    # Verificar que el usuario existe y es artista
    user_account = repo.get_account_by_id(session, user_id)
    if not user_account:
        raise NotFoundError("Usuario no encontrado")

    if user_account.role != UserRole.ARTIST:
        raise ValidationError("Solo los artistas modificar sus fotos")

    # Verificar cuántas fotos ya tiene
    current_photos = repo.get_artist_photos(session, user_id)
    if len(current_photos) >= 5:
        raise ValidationError("Máximo 5 fotos permitidas. Elimina una foto antes de agregar otra.")

    next_position = len(current_photos) + 1

    timestamp = int(time.time() * 1000)  # timestamp en millisegundos
    unique_suffix = uuid4().hex[:8]  # 8 caracteres únicos
    unique_public_id = f"{user_id}_{timestamp}_{unique_suffix}"

    # Subir la foto a Cloudinary
    try:
        uploaded_url = cloudinary.uploader.upload(photo_file_bytes, folder="artist-photos", public_id=unique_public_id, overwrite=False, resource_type="image")["secure_url"]

        if not uploaded_url:
            raise FileUploadError("Error al guardar la foto del artista")

        repo.add_artist_photo(session, user_id, uploaded_url, next_position)

        return {"message": "Foto agregada exitosamente", "photo_url": uploaded_url, "position": next_position, "total_photos": len(current_photos) + 1}

    except Exception as e:
        session.rollback()
        raise FileUploadError(f"Error al subir la foto: {str(e)}")


def delete_artist_photo(session: Session, user_id: UUID, photo_url: str) -> dict[str, str | int]:
    user_account = repo.get_account_by_id(session, user_id)
    if not user_account:
        raise NotFoundError("Usuario no encontrado")

    if user_account.role != UserRole.ARTIST:
        raise ValidationError("Solo los artistas pueden eliminar sus fotos")

    photo = repo.get_artist_photo_by_url(session, user_id, photo_url)
    if not photo:
        raise NotFoundError("Foto no encontrada")

    try:
        deleted_position = photo.position
        # Eliminar de Cloudinary
        # Extraer public_id de la URL
        url_parts = photo_url.split("/")
        if "artist-photos" in url_parts:
            public_id_with_extension = url_parts[-1]  # Último elemento
            public_id = public_id_with_extension.split(".")[0]  # Remover extensión
            full_public_id = f"artist-photos/{public_id}"
        else:
            # Fallback para URLs diferentes
            public_id = photo_url.split("/")[-1].split(".")[0]
            full_public_id = f"artist-photos/{public_id}"

        cloudinary.uploader.destroy(full_public_id)

        repo.delete_artist_photo(session, user_id, photo_url)

        # Reordenar las posiciones de las fotos restantes
        remaining_photos = repo.get_artist_photos(session, user_id)
        photos_to_reorder = [p for p in remaining_photos if p.position > deleted_position]

        # Actualizar posiciones de las fotos que estaban después
        for photo in photos_to_reorder:
            new_position = photo.position - 1
            repo.update_photo_position(session, photo.id, new_position)

        return {"message": "Foto eliminada exitosamente", "remaining_photos": len(remaining_photos)}

    except Exception as e:
        session.rollback()
        raise FileUploadError(f"Error al eliminar la foto: {str(e)}")


def reorder_artist_photos(session: Session, user_id: UUID, photo_urls: List[str]) -> dict[str, str | list[str]]:
    user_account = repo.get_account_by_id(session, user_id)
    if not user_account:
        raise NotFoundError("Usuario no encontrado")

    if user_account.role != UserRole.ARTIST:
        raise ValidationError("Solo los artistas pueden reordenar sus fotos")

    current_photos = repo.get_artist_photos(session, user_id)
    current_urls = {photo.url for photo in current_photos}

    for url in photo_urls:
        if url not in current_urls:
            raise ValidationError(f"Foto no encontrada: {url}")

    if len(photo_urls) != len(current_photos):
        raise ValidationError("Debe incluir todas las fotos en el reordenamiento")

    try:
        # Actualizar las posiciones
        for position, url in enumerate(photo_urls, 1):
            repo.update_photo_position_by_url(session, user_id, url, position)

        return {"message": "Fotos reordenadas exitosamente", "new_order": photo_urls}

    except Exception as e:
        session.rollback()
        raise ValidationError(f"Error al reordenar fotos: {str(e)}")


def follow_user(session: Session, current_user_id: UUID, user_id: UUID) -> MessageResponse:
    if current_user_id == user_id:
        raise ValidationError("No puedes seguirte a ti mismo.")

    followed = repo.get_profile_by_id(session, user_id)
    if not followed:
        raise NotFoundError("Usuario a seguir no encontrado")

    is_now_following = repo.toggle_follow(session, current_user_id, user_id)
    if is_now_following:
        return MessageResponse(message=f"Ahora sigues a {followed.username}")
    else:
        return MessageResponse(message=f"Dejaste de seguir a {followed.username}")


def get_followers(session: Session, user_id: UUID, current_user_id: UUID) -> FollowsListResponse:
    followers = repo.get_followers(session, user_id, current_user_id)
    return FollowsListResponse(follows=followers)


def get_following(session: Session, user_id: UUID, current_user_id: UUID) -> FollowsListResponse:
    following = repo.get_following(session, user_id, current_user_id)
    return FollowsListResponse(follows=following)

def change_history_preferences(session: Session, user_id: UUID) -> MessageResponse:
    account = repo.change_history_preferences(session, user_id)
    if not account:
        raise NotFoundError("Cuenta de usuario no encontrada")
    status = "activado" if account.preferences & 0b1 else "desactivado"
    return MessageResponse(message=f"Historial {status} exitosamente.")