import pytest
from fastapi import status
from httpx import AsyncClient

from tests.integral.conftest import TEST_BASE_URL, TestArtist, TestUser, auth_headers


@pytest.mark.asyncio
class TestPutArtistPhotosReorder:
    """Tests for PUT /artist/photos/reorder endpoint."""

    async def test_reorder_photos_success(self, async_client: AsyncClient, test_artist_full: TestArtist) -> None:
        """Reorder all existing artist photos successfully returns the new order."""
        current_urls = [p.url for p in test_artist_full.photos]
        new_order = list(reversed(current_urls))

        response = await async_client.put(
            f"{TEST_BASE_URL}/artist/photos/reorder",
            headers=auth_headers(test_artist_full.id, role="artist"),
            json={"photos": new_order},
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            "message": "Fotos reordenadas exitosamente",
            "new_order": new_order,
        }

    async def test_reorder_photos_length_mismatch_returns_400(self, async_client: AsyncClient, test_artist_full: TestArtist) -> None:
        """Sending a different number of URLs than current photos returns 400."""
        too_few = [test_artist_full.photos[0].url]

        response = await async_client.put(
            f"{TEST_BASE_URL}/artist/photos/reorder",
            headers=auth_headers(test_artist_full.id, role="artist"),
            json={"photos": too_few},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            "type": "about:blank",
            "title": "Bad request error",
            "status": status.HTTP_400_BAD_REQUEST,
            "detail": "Debe incluir todas las fotos en el reordenamiento",
            "instance": "/artist/photos/reorder",
        }

    async def test_reorder_photos_with_unknown_url_returns_400(self, async_client: AsyncClient, test_artist_full: TestArtist) -> None:
        """Including a URL that doesn't belong to the artist returns 400."""
        current_urls = [p.url for p in test_artist_full.photos]
        invalid_order = current_urls[:-1] + ["https://example.com/not-mine.jpg"]

        response = await async_client.put(
            f"{TEST_BASE_URL}/artist/photos/reorder",
            headers=auth_headers(test_artist_full.id, role="artist"),
            json={"photos": invalid_order},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["title"] == "Bad request error"
        assert response.json()["status"] == status.HTTP_400_BAD_REQUEST
        assert "Foto no encontrada" in response.json()["detail"]
        assert response.json()["instance"] == "/artist/photos/reorder"

    async def test_reorder_photos_non_artist_returns_400(self, async_client: AsyncClient, test_listener_minimal: TestUser) -> None:
        """Listeners cannot reorder photos and receive a 400 error."""
        response = await async_client.put(
            f"{TEST_BASE_URL}/artist/photos/reorder",
            headers=auth_headers(test_listener_minimal.id, role="listener"),
            json={"photos": ["https://example.com/1.jpg"]},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            "type": "about:blank",
            "title": "Bad request error",
            "status": status.HTTP_400_BAD_REQUEST,
            "detail": "Solo los artistas pueden reordenar sus fotos",
            "instance": "/artist/photos/reorder",
        }

    async def test_reorder_photos_unauthenticated_returns_401(self, async_client: AsyncClient) -> None:
        """Missing token returns 401 authentication error."""
        response = await async_client.put(
            f"{TEST_BASE_URL}/artist/photos/reorder",
            json={"photos": ["https://example.com/1.jpg"]},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json() == {
            "type": "about:blank",
            "title": "Authentication Error",
            "status": status.HTTP_401_UNAUTHORIZED,
            "detail": "Token de autenticación invalido o no proporcionado",
            "instance": "/artist/photos/reorder",
        }
