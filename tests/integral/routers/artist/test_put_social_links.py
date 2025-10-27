import pytest
from fastapi import status
from httpx import AsyncClient

from tests.integral.conftest import TEST_BASE_URL, TestArtist, TestUser, auth_headers


@pytest.mark.asyncio
class TestPutSocialLinks:
    """Tests for PUT /artist/social-links endpoint."""

    async def test_update_social_links_success(self, async_client: AsyncClient, test_artist_full: TestArtist) -> None:
        """Update artist social links successfully returns 204 with no content."""
        data = {"links": ["https://social1.com/x", "https://social2.com/y"]}
        response = await async_client.put(
            f"{TEST_BASE_URL}/artist/social-links",
            headers=auth_headers(test_artist_full.id, role="artist"),
            json=data,
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert response.text == ""

    async def test_update_social_links_ignores_blank_entries(self, async_client: AsyncClient, test_artist_full: TestArtist) -> None:
        """Blank links are ignored and still return 204."""
        data = {"links": ["   ", "https://valid.com"]}
        response = await async_client.put(
            f"{TEST_BASE_URL}/artist/social-links",
            headers=auth_headers(test_artist_full.id, role="artist"),
            json=data,
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT

    async def test_update_social_links_invalid_url_returns_400(self, async_client: AsyncClient, test_artist_full: TestArtist) -> None:
        """Invalid URL format should return 400 with validation error message."""
        data = {"links": ["notaurl"]}
        response = await async_client.put(
            f"{TEST_BASE_URL}/artist/social-links",
            headers=auth_headers(test_artist_full.id, role="artist"),
            json=data,
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            "type": "about:blank",
            "title": "Bad request error",
            "status": status.HTTP_400_BAD_REQUEST,
            "detail": "El link 'notaurl' no es una URL válida.",
            "instance": "/artist/social-links",
        }

    async def test_update_social_links_non_artist_returns_404(self, async_client: AsyncClient, test_listener_minimal: TestUser) -> None:
        """Non-artist users can't update social links and get 404 per service contract."""
        data = {"links": ["https://valid.com"]}
        response = await async_client.put(
            f"{TEST_BASE_URL}/artist/social-links",
            headers=auth_headers(test_listener_minimal.id, role="listener"),
            json=data,
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json() == {
            "type": "about:blank",
            "title": "Resource Not Found",
            "status": status.HTTP_404_NOT_FOUND,
            "detail": "Solo los artistas pueden modificar sus redes sociales",
            "instance": "/artist/social-links",
        }

    async def test_update_social_links_unauthenticated_returns_401(self, async_client: AsyncClient) -> None:
        """Missing token should return 401 from authentication middleware."""
        data = {"links": ["https://valid.com"]}
        response = await async_client.put(
            f"{TEST_BASE_URL}/artist/social-links",
            json=data,
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json() == {
            "type": "about:blank",
            "title": "Authentication Error",
            "status": status.HTTP_401_UNAUTHORIZED,
            "detail": "Token de autenticación invalido o no proporcionado",
            "instance": "/artist/social-links",
        }
