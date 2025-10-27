from typing import Any
import uuid
from httpx import AsyncClient
import pytest
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from tests.integral.conftest import TEST_BASE_URL, TestArtist, TestUser, auth_headers


@pytest.mark.asyncio
class TestGetUser:
    """Tests for the GET /{user_id} endpoint."""

    async def test_get_existing_listener(self, async_client: AsyncClient, test_listener_full: TestUser) -> None:
        """Successfully retrieve an existing listener profile."""
        response = await async_client.get(f"{TEST_BASE_URL}/{test_listener_full.id}", headers=auth_headers(test_listener_full.id, 'listener'))

        assert response.status_code == status.HTTP_200_OK, \
            f"Expected status code 200, got {response.status_code}. Response: {response.text}"
        
        response_data = response.json()
        expected_data: dict[str, Any] = {
            "id": str(test_listener_full.id),
            "role": test_listener_full.account.role,
            "username": test_listener_full.profile.username,
            "profilePhoto": test_listener_full.profile.profile_photo,
            "bio": test_listener_full.profile.bio,
            "followersCount": test_listener_full.profile.followers_count,
            "followingCount": test_listener_full.profile.following_count,
            "isFollowing": False,
            "photos": [],
            "links": []
        }

        for field, expected_value in expected_data.items():
            assert field in response_data, f"Field '{field}' not found in response"
            assert response_data[field] == expected_value, \
                f"Mismatch in field '{field}': expected {expected_value}, got {response_data[field]}"

    async def test_get_existing_artist(self, async_client: AsyncClient, test_artist_full: TestArtist) -> None:
        """Successfully retrieve an existing artist profile."""
        response = await async_client.get(f"{TEST_BASE_URL}/{test_artist_full.id}", headers=auth_headers(test_artist_full.id, 'artist'))

        assert response.status_code == status.HTTP_200_OK, \
            f"Expected status code 200, got {response.status_code}. Response: {response.text}"
        
        response_data = response.json()
        expected_data: dict[str, Any] = {
            "id": str(test_artist_full.id),
            "role": test_artist_full.account.role,
            "username": test_artist_full.profile.username,
            "profilePhoto": test_artist_full.profile.profile_photo,
            "bio": test_artist_full.profile.bio,
            "followersCount": test_artist_full.profile.followers_count,
            "followingCount": test_artist_full.profile.following_count,
            "isFollowing": False,
            "photos": [photo.url for photo in test_artist_full.photos],
            "links": [link.url for link in test_artist_full.links]
        }

        for field, expected_value in expected_data.items():
            assert field in response_data, f"Field '{field}' not found in response"
            assert response_data[field] == expected_value, \
                f"Mismatch in field '{field}': expected {expected_value}, got {response_data[field]}"
    
    async def test_get_nonexistent_account(self, async_client: AsyncClient, test_listener_full: TestUser) -> None:
        """Attempt to retrieve a non-existent user profile."""
        non_existent_user_id = uuid.UUID("00000000-0000-0000-0000-000000000000")
        response = await async_client.get(f"{TEST_BASE_URL}/{non_existent_user_id}", headers=auth_headers(test_listener_full.id, 'listener'))

        assert response.status_code == status.HTTP_404_NOT_FOUND, \
            f"Expected status code 404, got {response.status_code}. Response: {response.text}"
        
        assert response.json() == {
            "detail": "Cuenta de usuario no encontrada",
            "instance": f"/{non_existent_user_id}",
            "status": status.HTTP_404_NOT_FOUND,
            "title": "Resource Not Found",
            "type": "about:blank"
        }
    
    async def test_get_nonexistent_profile(self, async_client: AsyncClient, test_listener_full: TestUser, test_artist_full: TestArtist, session: AsyncSession) -> None:
        """Attempt to retrieve a user profile that does not exist."""
        await session.delete(test_artist_full.profile)
        await session.commit()
        response = await async_client.get(f"{TEST_BASE_URL}/{test_artist_full.id}", headers=auth_headers(test_listener_full.id, 'listener'))

        assert response.status_code == status.HTTP_404_NOT_FOUND, \
            f"Expected status code 404, got {response.status_code}. Response: {response.text}"

        assert response.json() == {
            "detail": "Perfil de usuario no encontrado",
            "instance": f"/{test_artist_full.id}",
            "status": status.HTTP_404_NOT_FOUND,
            "title": "Resource Not Found",
            "type": "about:blank"
        }