import time
from typing import Any, List, Union
from uuid import UUID, uuid4

import cloudinary.uploader
from pydantic import AnyUrl
from pydantic import ValidationError as PydanticValidationError
from sqlmodel import Session

import app.repositories.users_repository as repo
from app.errors.exceptions import FileUploadError, NotFoundError, ProfileAlreadyExistsError, UsernameTakenError, ValidationError
from app.models.user import UserProfile, UserRole
from app.schemas.artist import ArtistProfileView
from app.schemas.message import MessageResponse
from app.schemas.profile_photo import ProfilePhotoResponse
from app.schemas.user import (
    ArtistProfileResponse,
    FollowsListResponse,
    ListenerProfileView,
    SearchUsersResponse,
    UserDetailedInfo,
    UserProfileCreate,
    UserProfileResponse,
    UserProfileUpdate,
    UserRoleUpdateResponse,
    UserSearchItem,
)


def get_all_users(session: Session, page: int, page_size: int) -> dict[str, Any]:
    users, total = repo.get_all_users(session, page, page_size)
    return {
        "users": [{"id": str(u[0]), "username": u[1], "email": u[2], "role": u[3], "status": u[4]} for u in users],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }


def get_user(session: Session, user_id: UUID) -> UserDetailedInfo:
    user = repo.get_account_by_id(session, user_id)
    if not user:
        raise NotFoundError("Usuario con id: {} no encontrado".format(user_id))
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
        country=user.country,
        birthdate=None if not user_profile else user_profile.birthdate,
        last_login=user.last_login,
        created_at=user.created_at,
        profile_photo=None if not user_profile else user_profile.profile_photo,
    )


def create_user_profile(session: Session, user_id: UUID, profile_data: UserProfileCreate) -> UserProfileResponse:
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
    user = repo.get_account_by_id(session, user_id)
    if not user:
        raise NotFoundError("Usuario con id: {} no encontrado".format(user_id))
    user.role = UserRole.ARTIST if user.role == UserRole.LISTENER else UserRole.LISTENER
    _ = repo.create_user_account(session, user)
    return UserRoleUpdateResponse(
        id=str(user.id),
        role=user.role,
    )


def delete_user(session: Session, user_id: UUID):
    account = repo.get_account_by_id(session, user_id)
    if not account:
        raise NotFoundError("Usuario con id: {} no encontrado".format(user_id))
    user_profile = repo.get_profile_by_id(session, user_id)
    if user_profile and user_profile.profile_photo:
        cloudinary.uploader.destroy(public_id=f"user-photo-profile/{user_id}")

    repo.delete_user_account(session, account)
    return None


def update_profile_picture(session: Session, user_id: UUID, photo_file_bytes: bytes) -> ProfilePhotoResponse:
    uploaded_url = cloudinary.uploader.upload(photo_file_bytes, folder="user-photo-profile", public_id=str(user_id), overwrite=True)["secure_url"]

    if not uploaded_url:
        raise FileUploadError("Error al guardar la foto de perfil")
    if not repo.update_profile_picture(session, user_id, uploaded_url):
        raise NotFoundError("Usuario con id: {} no encontrado".format(user_id))

    return ProfilePhotoResponse(profile_photo=uploaded_url)


def get_me(session: Session, user_id: UUID) -> Union[UserProfileResponse, ArtistProfileResponse]:
    profile = repo.get_profile_by_id(session, user_id)
    if not profile:
        raise NotFoundError("Perfil no encontrado")

    user_account = repo.get_account_by_id(session, user_id)
    if user_account and user_account.role == UserRole.LISTENER:
        return UserProfileResponse.model_validate(profile)

    response_data = {
        "id": profile.id,
        "username": profile.username,
        "full_name": profile.full_name,
        "birthdate": profile.birthdate,
        "gender": profile.gender,
        "phone_number": profile.phone_number,
        "address": profile.address,
        "country": user_account.country,
        "profile_photo": profile.profile_photo,
        "bio": profile.bio,
        "followers_count": profile.followers_count,
        "following_count": profile.following_count,
    }

    if user_account.role == UserRole.ARTIST:
        try:
            photos = repo.get_artist_photos(session, user_id)
            photos_sorted = sorted(photos, key=lambda p: p.position)
            links = repo.get_artist_links(session, user_id)

            artist_data = {**response_data, "photos": [photo.url for photo in photos_sorted], "links": [link.url for link in links]}
            return ArtistProfileResponse(**artist_data)
        except Exception as e:
            print(f"Error obteniendo datos de artista: {e}")
            artist_data = {**response_data, "photos": [], "links": []}
            return ArtistProfileResponse(**artist_data)
    else:
        return UserProfileResponse(**response_data)  # Oyente


def search_users(session: Session, query: str, role: str | None, page: int, page_size: int) -> SearchUsersResponse:
    users = repo.search_users(session, query, role, page, page_size)
    return SearchUsersResponse(
        users=[UserSearchItem(id=str(u.id), role=u.role, username=u.username, profile_photo=u.profile_photo, similarity_score=u.similarity_score) for u in users],
    )


def update_me(session: Session, user_id: UUID, data: UserProfileUpdate) -> UserProfileResponse:
    profile = repo.get_user_profile_by_user_id(session, user_id)
    if not profile:
        raise NotFoundError("Perfil no encontrado")

    # Obtener datos actuales para validar campos requeridos
    current_data = {
        "username": profile.username,
        "full_name": profile.full_name,
        "birthdate": profile.birthdate,
        "gender": profile.gender,
    }

    # Aplicar nuevos datos
    update_data = data.model_dump(exclude_unset=True)
    updated_data = {**current_data, **update_data}

    # Validar campos requeridos después de la actualización
    required_fields = {
        "username": "El nombre de usuario es obligatorio",
        "full_name": "El nombre completo es obligatorio",
        "birthdate": "La fecha de nacimiento es obligatoria",
        "gender": "El género es obligatorio",
    }

    for field, error_msg in required_fields.items():
        if not updated_data.get(field):
            raise ValidationError(error_msg)

    # Validar username único si cambió
    if data.username and data.username.strip() and data.username != profile.username:
        existing_username = repo.get_profile_by_username(session, data.username)
        if existing_username:
            raise UsernameTakenError("El nombre de usuario ya está en uso")

    updated_profile = repo.update_user_profile(session, user_id, update_data)
    return UserProfileResponse.model_validate(updated_profile)


def get_artist(session: Session, artist_id: UUID, current_user_id: UUID) -> ArtistProfileView:
    account = repo.get_account_by_id(session, artist_id)
    if not account or account.role != UserRole.ARTIST:
        raise NotFoundError("Artista no encontrado")

    profile = repo.get_profile_by_id(session, artist_id)
    if not profile:
        raise NotFoundError("Perfil de artista no encontrado")

    photos = repo.get_artist_photos(session, artist_id)
    photos_sorted = sorted(photos, key=lambda p: p.position)
    links = repo.get_artist_links(session, artist_id)

    return ArtistProfileView(
        id=str(artist_id),
        username=profile.username,
        profile_photo=profile.profile_photo,
        bio=profile.bio,
        followers_count=profile.followers_count,
        following_count=profile.following_count,
        photos=[photo.url for photo in photos_sorted],
        links=[link.url for link in links],
        is_following=repo.is_following(session, current_user_id, artist_id),
    )


def visualize_user(session: Session, user_id: UUID, current_user_id: UUID) -> ListenerProfileView:
    account = repo.get_account_by_id(session, user_id)
    if not account or account.role != UserRole.LISTENER:
        raise NotFoundError("Usuario oyente no encontrado")
    profile = repo.get_profile_by_id(session, user_id)
    if not profile:
        raise NotFoundError("Usuario no encontrado")
    is_following = repo.is_following(session, current_user_id, user_id)
    return ListenerProfileView(
        id=str(user_id),
        username=profile.username,
        profile_photo=profile.profile_photo,
        bio=profile.bio,
        followers_count=profile.followers_count,
        following_count=profile.following_count,
        is_following=is_following,
    )


def update_artist_social_links(session, user_id, data):
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


def add_artist_photo(session: Session, user_id: UUID, photo_file_bytes: bytes):
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


def delete_artist_photo(session: Session, user_id: UUID, photo_url: str):
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


def reorder_artist_photos(session: Session, user_id: UUID, photo_urls: List[str]):
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

    try:
        is_now_following = repo.toggle_follow(session, current_user_id, user_id)
        session.commit()

        if is_now_following:
            return MessageResponse(message=f"Ahora sigues a {followed.username}")
        else:
            return MessageResponse(message=f"Dejaste de seguir a {followed.username}")

    except Exception as e:
        session.rollback()
        raise ValidationError(f"Error al seguir o dejar de seguir al usuario: {str(e)}")


def get_followers(session: Session, user_id: UUID, current_user_id: UUID) -> FollowsListResponse:
    followers = repo.get_followers(session, user_id, current_user_id)
    return FollowsListResponse(follows=followers)


def get_following(session: Session, user_id: UUID, current_user_id: UUID) -> FollowsListResponse:
    following = repo.get_following(session, user_id, current_user_id)
    return FollowsListResponse(follows=following)
