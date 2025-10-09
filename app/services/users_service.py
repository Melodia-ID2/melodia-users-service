from typing import Any
from uuid import UUID
from pydantic import AnyUrl, ValidationError
from app.errors.exceptions import NotFoundError, FileUploadError
from pydantic import AnyUrl, ValidationError as PydanticValidationError
from app.models.user import UserProfile, UserRole
from sqlmodel import Session
import cloudinary.uploader
from app.schemas.user import ListenerPublicProfile, UserDetailedInfo, UserProfileCreate, UserProfileResponse, UserProfileUpdate, UserRoleUpdateResponse, UserSearchItem, SearchUsersResponse
from app.schemas.artist import ArtistPublicProfile
from app.schemas.photo_profile import PhotoProfileResponse
import app.repositories.users_repository as repo
from app.errors.exceptions import UsernameTakenError, ProfileAlreadyExistsError

def get_all_users(session: Session, page: int, page_size: int) -> dict[str, Any]:
    users, total = repo.get_all_users(session, page, page_size)
    return {
        "users": [
            {"id": str(u[0]), "username": u[1], "email": u[2], "role": u[3], "status": u[4]} for u in users
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }


def get_user(session: Session, user_id: UUID) -> UserDetailedInfo:
    user = repo.get_user_account_by_id(session, user_id)
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
        raise NotFoundError("Usuario con id: {} no encontrado".format(user_id))
    user.role = UserRole.ARTIST if user.role == UserRole.LISTENER else UserRole.LISTENER
    _ = repo.create_user_account(session, user)
    return UserRoleUpdateResponse(
        id=str(user.id),
        role=user.role,
    )

def delete_user(session: Session, user_id: UUID):
    account = repo.get_user_account_by_id(session, user_id)
    if not account:
        raise NotFoundError("Usuario con id: {} no encontrado".format(user_id))
    user_profile = repo.get_profile_by_id(session, user_id)
    if user_profile and user_profile.photo_profile:
        cloudinary.uploader.destroy(public_id=f"user-photo-profile/{user_id}")

    repo.delete_user_account(session, account)
    return None


def update_photo_profile(session: Session,user_id: UUID, photo_file_bytes: bytes) -> PhotoProfileResponse:
    uploaded_url = cloudinary.uploader.upload(
            photo_file_bytes,
            folder="user-photo-profile",
            public_id=str(user_id),
            overwrite=True
        )["secure_url"]

    if not uploaded_url:
        raise FileUploadError("Error al guardar la foto de perfil")
    if not repo.update_photo_profile(session,user_id, uploaded_url):
        raise NotFoundError("Usuario con id: {} no encontrado".format(user_id))


    return PhotoProfileResponse(photo_profile=uploaded_url)

def get_me(session: Session, user_id: UUID) -> UserProfileResponse:
    profile = repo.get_profile_by_id(session, user_id)
    if not profile:
        raise NotFoundError("Perfil no encontrado")
    response = UserProfileResponse.model_validate(profile)
    response.profile_photo = profile.photo_profile
    return response


def search_users(session: Session, query: str, role: str | None, page: int, page_size: int) -> SearchUsersResponse:
    users = repo.search_users(session, query, role, page, page_size)
    return SearchUsersResponse(
        users=[UserSearchItem(id=str(u.id), role=u.role, username=u.username, profile_photo=u.photo_profile) for u in users],
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
        "gender": "El género es obligatorio"
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

def get_artist(session, artist_id):
    account = repo.get_user_account_by_id(session, artist_id)
    if not account or account.role != UserRole.ARTIST:
        raise NotFoundError("Artista no encontrado")

    profile = repo.get_profile_by_id(session, artist_id)
    if not profile:
        raise NotFoundError("Perfil de artista no encontrado")

    photos = repo.get_artist_photos(session, artist_id)
    photos_sorted = sorted(photos, key=lambda p: p.position)
    links = repo.get_artist_links(session, artist_id)

    return ArtistPublicProfile(
        username=profile.username,
        full_name=profile.full_name,
        photo_profile=profile.photo_profile,
        bio=profile.bio,
        photos=[photo.url for photo in photos_sorted],
        links=[link.url for link in links],
    )

def visualize_user(session, user_id):
    account = repo.get_user_account_by_id(session, user_id)
    if not account or account.role != UserRole.LISTENER:
        raise NotFoundError("Usuario oyente no encontrado")
    profile = repo.get_profile_by_id(session, user_id)
    if not profile:
        raise NotFoundError("Usuario no encontrado")
    return ListenerPublicProfile(
        username=profile.username,
        photo_profile=profile.photo_profile,
        bio=profile.bio,
    )

def update_artist_social_links(session, user_id, data):
    account = repo.get_user_account_by_id(session, user_id)
    if not account or account.role != UserRole.ARTIST:
        raise NotFoundError("Solo los artistas pueden modificar sus redes sociales")

    for url in data.links:
        try:
            AnyUrl(url=url)
        except PydanticValidationError:
            raise ValidationError(f"El link '{url}' no es una URL válida.")

    repo.delete_artist_social_links(session, user_id)
    for url in data.links:
        repo.add_artist_social_link(session, user_id, url)
    return None

def update_artist_photos(session, user_id, data):
    account = repo.get_user_account_by_id(session, user_id)
    if not account or account.role != UserRole.ARTIST:
        raise NotFoundError("Solo los artistas pueden modificar sus fotos")

    if len(data.photos) > 5:
        raise ValidationError("Solo puedes guardar hasta 5 fotos de artista.")

    # Elimina las fotos anteriores
    repo.delete_artist_photos(session, user_id)
    # Agrega las nuevas fotos en el orden recibido
    for position, url in enumerate(data.photos):
        repo.add_artist_photo(session, user_id, url, position)
    return None