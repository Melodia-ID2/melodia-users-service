from unittest.mock import Mock

import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.userprofile import ArtistPhoto
from tests.integral.conftest import TEST_BASE_URL, TestArtist, TestUser, auth_headers


@pytest.mark.asyncio
class TestDeleteArtistPhotos:
    """Tests for DELETE /artist/photos endpoint."""

    async def test_delete_artist_photo_success(self, async_client: AsyncClient, test_artist_full: TestArtist, monkeypatch: pytest.MonkeyPatch, session: AsyncSession) -> None:
        """Delete an existing artist photo and update remaining count."""
        mock_destroy = Mock()
        monkeypatch.setattr("app.services.users_service.cloudinary.uploader.destroy", mock_destroy)

        target_url = test_artist_full.photos[0].url
        initial_count = len(test_artist_full.photos)

        response = await async_client.request(
            "DELETE",
            f"{TEST_BASE_URL}/artist/photos",
            headers=auth_headers(test_artist_full.id, role="artist"),
            json={"photo_url": target_url},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "Foto eliminada exitosamente"
        assert data["remaining_photos"] == initial_count - 1

        await session.commit()
        session.expire_all()
        photos = (await session.execute(select(ArtistPhoto).where(ArtistPhoto.artist_id == test_artist_full.id))).scalars().all()
        assert all(p.url != target_url for p in photos)

        assert mock_destroy.called
        arg = mock_destroy.call_args[0][0]
        assert isinstance(arg, str)
        assert arg.startswith("artist-photos/")

    async def test_delete_artist_photo_non_artist_returns_400(self, async_client: AsyncClient, test_listener_minimal: TestUser, monkeypatch: pytest.MonkeyPatch) -> None:
        """Listeners cannot delete artist photos."""
        mock_destroy = Mock()
        monkeypatch.setattr("app.services.users_service.cloudinary.uploader.destroy", mock_destroy)

        response = await async_client.request(
            "DELETE",
            f"{TEST_BASE_URL}/artist/photos",
            headers=auth_headers(test_listener_minimal.id, role="listener"),
            json={"photo_url": "https://example.com/photo.jpg"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            "type": "about:blank",
            "title": "Bad request error",
            "status": status.HTTP_400_BAD_REQUEST,
            "detail": "Solo los artistas pueden eliminar sus fotos",
            "instance": "/artist/photos",
        }
        mock_destroy.assert_not_called()

    async def test_delete_artist_photo_not_found_returns_404(self, async_client: AsyncClient, test_artist_full: TestArtist, monkeypatch: pytest.MonkeyPatch) -> None:
        """Deleting a non-existing photo returns 404."""
        mock_destroy = Mock()
        monkeypatch.setattr("app.services.users_service.cloudinary.uploader.destroy", mock_destroy)

        response = await async_client.request(
            "DELETE",
            f"{TEST_BASE_URL}/artist/photos",
            headers=auth_headers(test_artist_full.id, role="artist"),
            json={"photo_url": "https://example.com/notfound.jpg"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json() == {
            "type": "about:blank",
            "title": "Resource Not Found",
            "status": status.HTTP_404_NOT_FOUND,
            "detail": "Foto no encontrada",
            "instance": "/artist/photos",
        }

    async def test_delete_artist_photo_unauthenticated_returns_401(self, async_client: AsyncClient) -> None:
        """Missing token returns 401 authentication error."""
        response = await async_client.request(
            "DELETE",
            f"{TEST_BASE_URL}/artist/photos",
            json={"photo_url": "https://example.com/photo.jpg"},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json() == {
            "type": "about:blank",
            "title": "Authentication Error",
            "status": status.HTTP_401_UNAUTHORIZED,
            "detail": "Token de autenticación invalido o no proporcionado",
            "instance": "/artist/photos",
        }
