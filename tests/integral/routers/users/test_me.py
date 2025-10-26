from typing import Any
from httpx import AsyncClient
import pytest
from fastapi import status

from tests.integral.conftest import TEST_BASE_URL, TestArtist, TestUser, auth_headers


@pytest.mark.asyncio
class TestGetCurrentUser:
    """Pruebas para el endpoint GET /me"""

    async def test_get_me_authenticated_with_complete_profile_listener(self, async_client: AsyncClient, test_listener_full: TestUser) -> None:
        """Obtener perfil del usuario autenticado exitosamente"""
        response = await async_client.get(f"{TEST_BASE_URL}/me", headers=auth_headers(test_listener_full, role='listener'))

        assert response.status_code == status.HTTP_200_OK, \
            f"Expected status code 200, got {response.status_code}. Response: {response.text}"

        response_data = response.json()
        expected_data: dict[str, Any] = {
            'id': str(test_listener_full.id),
            'username': test_listener_full.profile.username,
            'fullName': test_listener_full.profile.full_name if test_listener_full.profile.full_name else "",
            'birthdate': test_listener_full.profile.birthdate.isoformat() if test_listener_full.profile.birthdate else None,
            'gender': test_listener_full.profile.gender.value if test_listener_full.profile.gender else None,
            'phoneNumber': test_listener_full.profile.phone_number,
            'address': test_listener_full.profile.address,
            'profilePhoto': test_listener_full.profile.profile_photo,
            'bio': test_listener_full.profile.bio,
            'country': test_listener_full.account.country.value,
            'followersCount': test_listener_full.profile.followers_count,
            'followingCount': test_listener_full.profile.following_count,
        }
        
        for field, expected_value in expected_data.items():
            assert field in response_data, f"Field '{field}' not found in response"
            assert response_data[field] == expected_value, \
                f"Mismatch in field '{field}': expected {expected_value}, got {response_data[field]}"

    async def test_get_me_authenticated_with_complete_profile_artist(self, async_client: AsyncClient, test_artist_full: TestArtist) -> None:
        """Obtener perfil del usuario autenticado exitosamente"""
        response = await async_client.get(f"{TEST_BASE_URL}/me", headers=auth_headers(test_artist_full, role='artist'))

        assert response.status_code == status.HTTP_200_OK, \
            f"Expected status code 200, got {response.status_code}. Response: {response.text}"

        response_data = response.json()
        expected_data: dict[str, Any] = {
            'id': str(test_artist_full.id),
            'username': test_artist_full.profile.username,
            'fullName': test_artist_full.profile.full_name if test_artist_full.profile.full_name else "",
            'birthdate': test_artist_full.profile.birthdate.isoformat() if test_artist_full.profile.birthdate else None,
            'gender': test_artist_full.profile.gender.value if test_artist_full.profile.gender else None,
            'phoneNumber': test_artist_full.profile.phone_number,
            'address': test_artist_full.profile.address,
            'profilePhoto': test_artist_full.profile.profile_photo,
            'bio': test_artist_full.profile.bio,
            'country': test_artist_full.account.country.value,
            'followersCount': test_artist_full.profile.followers_count,
            'followingCount': test_artist_full.profile.following_count,
            'photos': [photo.url for photo in sorted(test_artist_full.photos, key=lambda p: p.position)],
            'links': [link.url for link in test_artist_full.links],
        }
        
        for field, expected_value in expected_data.items():
            assert field in response_data, f"Field '{field}' not found in response"
            assert response_data[field] == expected_value, \
                f"Mismatch in field '{field}': expected {expected_value}, got {response_data[field]}"    

    async def test_get_me_authenticated_with_minimal_profile_listener(self, async_client: AsyncClient, test_listener_minimal: TestUser) -> None:
        """Obtener perfil del usuario autenticado exitosamente"""
        response = await async_client.get(f"{TEST_BASE_URL}/me", headers=auth_headers(test_listener_minimal, role='listener'))

        assert response.status_code == status.HTTP_200_OK, \
            f"Expected status code 200, got {response.status_code}. Response: {response.text}"

        response_data = response.json()
        expected_data: dict[str, Any] = {
            'id': str(test_listener_minimal.id),
            'username': None,
            'fullName': None,
            'birthdate': None,
            'gender': test_listener_minimal.profile.gender.value,
            'phoneNumber': None,
            'address': None,
            'profilePhoto': None,
            'bio': None,
            'country': test_listener_minimal.account.country.value,
            'followersCount': 0,
            'followingCount': 0,
        }
        
        for field, expected_value in expected_data.items():
            assert field in response_data, f"Field '{field}' not found in response"
            assert response_data[field] == expected_value, \
                f"Mismatch in field '{field}': expected {expected_value}, got {response_data[field]}"
