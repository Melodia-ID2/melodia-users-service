from unittest.mock import Mock

import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.userprofile import ArtistPhoto
from tests.integral.conftest import TEST_BASE_URL, TestArtist, TestUser, auth_headers


@pytest.mark.asyncio
class TestPutArtistPhotos:
    """Tests for PUT /artist/photos endpoint."""

    async def test_add_artist_photo_success(self, async_client: AsyncClient, test_artist_full: TestArtist, monkeypatch: pytest.MonkeyPatch, session: AsyncSession) -> None:
        """Add a photo successfully and persist to DB, returning 201 and metadata."""
        new_url = f"https://res.cloudinary.com/test/image/upload/v123/artist-photos/{test_artist_full.id}_new.jpg"
        mock_upload = Mock(return_value={"secure_url": new_url})
        monkeypatch.setattr("app.services.users_service.cloudinary.uploader.upload", mock_upload)

        fake_image = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
        files = {"file": ("photo.jpg", fake_image, "image/jpeg")}

        response = await async_client.put(
            f"{TEST_BASE_URL}/artist/photos",
            headers=auth_headers(test_artist_full.id, role="artist"),
            files=files,
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["message"] == "Foto agregada exitosamente"
        assert data["photo_url"] == new_url
        assert data["position"] == len(test_artist_full.photos) + 1
        assert data["total_photos"] == len(test_artist_full.photos) + 1

        await session.commit()
        session.expire_all()
        photos = (await session.execute(select(ArtistPhoto).where(ArtistPhoto.artist_id == test_artist_full.id))).scalars().all()
        assert any(p.url == new_url for p in photos)

        mock_upload.assert_called_once()

    async def test_add_artist_photo_limit_exceeded(self, async_client: AsyncClient, test_artist_full: TestArtist, monkeypatch: pytest.MonkeyPatch) -> None:
        """When adding beyond 5 photos, return 400 with validation message."""
        mock_upload = Mock(return_value={"secure_url": "https://res.cloudinary.com/test/image/upload/v123/artist-photos/any.jpg"})
        monkeypatch.setattr("app.services.users_service.cloudinary.uploader.upload", mock_upload)

        fake_image = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
        files = {"file": ("photo.jpg", fake_image, "image/jpeg")}

        await async_client.put(f"{TEST_BASE_URL}/artist/photos", headers=auth_headers(test_artist_full.id, role="artist"), files=files)
        await async_client.put(f"{TEST_BASE_URL}/artist/photos", headers=auth_headers(test_artist_full.id, role="artist"), files=files)

        response = await async_client.put(f"{TEST_BASE_URL}/artist/photos", headers=auth_headers(test_artist_full.id, role="artist"), files=files)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            "type": "about:blank",
            "title": "Bad request error",
            "status": status.HTTP_400_BAD_REQUEST,
            "detail": "Máximo 5 fotos permitidas. Elimina una foto antes de agregar otra.",
            "instance": "/artist/photos",
        }

    async def test_add_artist_photo_non_artist_returns_400(self, async_client: AsyncClient, test_listener_minimal: TestUser, monkeypatch: pytest.MonkeyPatch) -> None:
        """Listeners cannot add artist photos, return 400 validation error."""
        mock_upload = Mock(return_value={"secure_url": "https://res.cloudinary.com/test/image/upload/v123/artist-photos/any.jpg"})
        monkeypatch.setattr("app.services.users_service.cloudinary.uploader.upload", mock_upload)

        fake_image = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
        files = {"file": ("photo.jpg", fake_image, "image/jpeg")}

        response = await async_client.put(
            f"{TEST_BASE_URL}/artist/photos",
            headers=auth_headers(test_listener_minimal.id, role="listener"),
            files=files,
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            "type": "about:blank",
            "title": "Bad request error",
            "status": status.HTTP_400_BAD_REQUEST,
            "detail": "Solo los artistas modificar sus fotos",
            "instance": "/artist/photos",
        }

    async def test_add_artist_photo_unauthenticated_returns_401(self, async_client: AsyncClient, monkeypatch: pytest.MonkeyPatch) -> None:
        """Missing token returns 401 authentication error."""
        mock_upload = Mock(return_value={"secure_url": "https://res.cloudinary.com/test/image/upload/v123/artist-photos/any.jpg"})
        monkeypatch.setattr("app.services.users_service.cloudinary.uploader.upload", mock_upload)

        fake_image = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
        files = {"file": ("photo.jpg", fake_image, "image/jpeg")}

        response = await async_client.put(f"{TEST_BASE_URL}/artist/photos", files=files)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json() == {
            "type": "about:blank",
            "title": "Authentication Error",
            "status": status.HTTP_401_UNAUTHORIZED,
            "detail": "Token de autenticación invalido o no proporcionado",
            "instance": "/artist/photos",
        }
        mock_upload.assert_not_called()

    async def test_add_artist_photo_cloudinary_failure(self, async_client: AsyncClient, test_artist_full: TestArtist, monkeypatch: pytest.MonkeyPatch) -> None:
        """When upload returns no URL, respond with 500 file upload error."""
        mock_upload = Mock(return_value={"secure_url": None})
        monkeypatch.setattr("app.services.users_service.cloudinary.uploader.upload", mock_upload)

        fake_image = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
        files = {"file": ("photo.jpg", fake_image, "image/jpeg")}

        response = await async_client.put(
            f"{TEST_BASE_URL}/artist/photos",
            headers=auth_headers(test_artist_full.id, role="artist"),
            files=files,
        )

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.json() == {
            "type": "about:blank",
            "title": "File Upload Error",
            "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "detail": "Error al guardar la foto del artista",
            "instance": "/artist/photos",
        }
