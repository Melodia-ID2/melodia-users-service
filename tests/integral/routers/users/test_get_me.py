from typing import Any
import uuid
from httpx import AsyncClient
import pytest
from fastapi import status

from tests.integral.conftest import TEST_BASE_URL, TestArtist, TestUser, auth_headers


@pytest.mark.asyncio
class TestGetCurrentUser:
    """Tests for the GET /me endpoint."""

    async def test_get_me_authenticated_with_complete_profile_listener(self, async_client: AsyncClient, test_listener_full: TestUser) -> None:
        """Successfully retrieve the authenticated user's profile."""
        response = await async_client.get(f"{TEST_BASE_URL}/me", headers=auth_headers(test_listener_full.id, role='listener'))

        assert response.status_code == status.HTTP_200_OK, \
            f"Expected status code 200, got {response.status_code}. Response: {response.text}"

        response_data = response.json()
        expected_data: dict[str, Any] = {
            'id': str(test_listener_full.id),
            'username': test_listener_full.profile.username,
            'fullName': test_listener_full.profile.full_name,
            'birthdate': test_listener_full.profile.birthdate.isoformat(),
            'gender': test_listener_full.profile.gender.value,
            'phoneNumber': test_listener_full.profile.phone_number,
            'address': test_listener_full.profile.address,
            'profilePhoto': test_listener_full.profile.profile_photo,
            'bio': test_listener_full.profile.bio,
            'followersCount': test_listener_full.profile.followers_count,
            'followingCount': test_listener_full.profile.following_count,
            'preferences': test_listener_full.account.preferences
        }
        
        for field, expected_value in expected_data.items():
            assert field in response_data, f"Field '{field}' not found in response"
            assert response_data[field] == expected_value, \
                f"Mismatch in field '{field}': expected {expected_value}, got {response_data[field]}"

    async def test_get_me_authenticated_with_complete_profile_artist(self, async_client: AsyncClient, test_artist_full: TestArtist) -> None:
        """Successfully retrieve the authenticated user's profile."""
        response = await async_client.get(f"{TEST_BASE_URL}/me", headers=auth_headers(test_artist_full.id, role='artist'))

        assert response.status_code == status.HTTP_200_OK, \
            f"Expected status code 200, got {response.status_code}. Response: {response.text}"

        response_data = response.json()
        expected_data: dict[str, Any] = {
            'id': str(test_artist_full.id),
            'username': test_artist_full.profile.username,
            'fullName': test_artist_full.profile.full_name,
            'birthdate': test_artist_full.profile.birthdate.isoformat(),
            'gender': test_artist_full.profile.gender.value,
            'phoneNumber': test_artist_full.profile.phone_number,
            'address': test_artist_full.profile.address,
            'profilePhoto': test_artist_full.profile.profile_photo,
            'bio': test_artist_full.profile.bio,
            'followersCount': test_artist_full.profile.followers_count,
            'followingCount': test_artist_full.profile.following_count,
            'photos': [photo.url for photo in sorted(test_artist_full.photos, key=lambda p: p.position)],
            'links': [link.url for link in test_artist_full.links],
            'preferences': test_artist_full.account.preferences
        }
        
        for field, expected_value in expected_data.items():
            assert field in response_data, f"Field '{field}' not found in response"
            assert response_data[field] == expected_value, \
                f"Mismatch in field '{field}': expected {expected_value}, got {response_data[field]}"    

    async def test_get_me_authenticated_with_minimal_profile_listener(self, async_client: AsyncClient, test_listener_minimal: TestUser) -> None:
        """Successfully retrieve the authenticated user's profile."""
        response = await async_client.get(f"{TEST_BASE_URL}/me", headers=auth_headers(test_listener_minimal.id, role='listener'))

        assert response.status_code == status.HTTP_200_OK, \
            f"Expected status code 200, got {response.status_code}. Response: {response.text}"

        response_data = response.json()
        expected_data: dict[str, Any] = {
            'id': str(test_listener_minimal.id),
            'username': test_listener_minimal.profile.username,
            'fullName': test_listener_minimal.profile.full_name,
            'birthdate': test_listener_minimal.profile.birthdate.isoformat(),
            'gender': test_listener_minimal.profile.gender.value,
            'phoneNumber': None,
            'address': None,
            'profilePhoto': None,
            'bio': None,
            'followersCount': 0,
            'followingCount': 0,
            'preferences': test_listener_minimal.account.preferences
        }
        
        for field, expected_value in expected_data.items():
            assert field in response_data, f"Field '{field}' not found in response"
            assert response_data[field] == expected_value, \
                f"Mismatch in field '{field}': expected {expected_value}, got {response_data[field]}"
    
    async def test_get_me_unauthenticated(self, async_client: AsyncClient) -> None:
        """Attempting to retrieve a profile without authentication should fail."""
        response = await async_client.get(f"{TEST_BASE_URL}/me")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json() == {
            "type": "about:blank",
            "title": "Authentication Error",
            "status": 401,
            "detail": "Token de autenticación invalido o no proporcionado",
            "instance": "/me"
        }
    

    async def test_get_me_unknown_user(self, async_client: AsyncClient) -> None:
        """Attempting to retrieve a profile for a non-existent user should fail."""
        response = await async_client.get(f"{TEST_BASE_URL}/me", headers=auth_headers(uuid.uuid4(), role='listener'))

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json() == {
            "type": "about:blank",
            "title": "Resource Not Found",
            "status": 404,
            "detail": "Usuario no encontrado",
            "instance": "/me"
        }
