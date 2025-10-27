import time
from uuid import UUID, uuid4

import cloudinary.uploader
from pydantic import AnyUrl
from pydantic import ValidationError as PydanticValidationError
from sqlmodel import Session

import app.repositories.artist_repository as artist_repo
import app.repositories.users_repository as users_repo
from app.errors.exceptions import FileUploadError, NotFoundError, ValidationError
from app.models.useraccount import UserRole
from app.schemas.artist import SocialLinksUpdateRequest


def update_artist_social_links(session: Session, user_id: UUID, data: SocialLinksUpdateRequest) -> None:
    account = users_repo.get_account_by_id(session, user_id)
    if not account or account.role != UserRole.ARTIST:
        raise NotFoundError("Solo los artistas pueden modificar sus redes sociales")

    for url in data.links:
        if url.strip():  # Solo validar URLs no vacías
            try:
                AnyUrl(url=url)
            except PydanticValidationError:
                raise ValidationError(f"El link '{url}' no es una URL válida.")

    valid_links = [url.strip() for url in data.links if url.strip()]

    artist_repo.update_artist_social_links(session, user_id, valid_links)

    return None


def add_artist_photo(session: Session, user_id: UUID, photo_file_bytes: bytes) -> dict[str, str | int]:
    """
    Agrega una foto al perfil del artista.
    Máximo 5 fotos permitidas.
    """
    # Verificar que el usuario existe y es artista
    user_account = users_repo.get_account_by_id(session, user_id)
    if not user_account:
        raise NotFoundError("Usuario no encontrado")

    if user_account.role != UserRole.ARTIST:
        raise ValidationError("Solo los artistas modificar sus fotos")

    # Verificar cuántas fotos ya tiene
    current_photos = artist_repo.get_artist_photos(session, user_id)
    if len(current_photos) >= 5:
        raise ValidationError("Máximo 5 fotos permitidas. Elimina una foto antes de agregar otra.")

    next_position = len(current_photos) + 1

    timestamp = int(time.time() * 1000)  # timestamp en millisegundos
    unique_suffix = uuid4().hex[:8]  # 8 caracteres únicos
    unique_public_id = f"{user_id}_{timestamp}_{unique_suffix}"

    # Subir la foto a Cloudinary
    uploaded_url = cloudinary.uploader.upload(photo_file_bytes, folder="artist-photos", public_id=unique_public_id, overwrite=False, resource_type="image")["secure_url"]

    if not uploaded_url:
        raise FileUploadError("Error al guardar la foto del artista")

    artist_repo.add_artist_photo(session, user_id, uploaded_url, next_position)

    return {"message": "Foto agregada exitosamente", "photo_url": uploaded_url, "position": next_position, "total_photos": len(current_photos) + 1}


def delete_artist_photo(session: Session, user_id: UUID, photo_url: str) -> dict[str, str | int]:
    user_account = users_repo.get_account_by_id(session, user_id)
    if not user_account:
        raise NotFoundError("Usuario no encontrado")

    if user_account.role != UserRole.ARTIST:
        raise ValidationError("Solo los artistas pueden eliminar sus fotos")

    photo = artist_repo.get_artist_photo_by_url(session, user_id, photo_url)
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

        artist_repo.delete_artist_photo(session, user_id, photo_url)

        # Reordenar las posiciones de las fotos restantes
        remaining_photos = artist_repo.get_artist_photos(session, user_id)
        photos_to_reorder = [p for p in remaining_photos if p.position > deleted_position]

        # Actualizar posiciones de las fotos que estaban después
        for photo in photos_to_reorder:
            new_position = photo.position - 1
            artist_repo.update_photo_position(session, photo.id, new_position)

        return {"message": "Foto eliminada exitosamente", "remaining_photos": len(remaining_photos)}

    except Exception as e:
        session.rollback()
        raise FileUploadError(f"Error al eliminar la foto: {str(e)}")


def reorder_artist_photos(session: Session, user_id: UUID, photo_urls: list[str]) -> dict[str, str | list[str]]:
    user_account = users_repo.get_account_by_id(session, user_id)
    if not user_account:
        raise NotFoundError("Usuario no encontrado")

    if user_account.role != UserRole.ARTIST:
        raise ValidationError("Solo los artistas pueden reordenar sus fotos")

    current_photos = artist_repo.get_artist_photos(session, user_id)
    current_urls = {photo.url for photo in current_photos}

    for url in photo_urls:
        if url not in current_urls:
            raise ValidationError(f"Foto no encontrada: {url}")

    if len(photo_urls) != len(current_photos):
        raise ValidationError("Debe incluir todas las fotos en el reordenamiento")

    try:
        # Actualizar las posiciones
        for position, url in enumerate(photo_urls, 1):
            artist_repo.update_photo_position_by_url(session, user_id, url, position)

        return {"message": "Fotos reordenadas exitosamente", "new_order": photo_urls}

    except Exception as e:
        session.rollback()
        raise ValidationError(f"Error al reordenar fotos: {str(e)}")
