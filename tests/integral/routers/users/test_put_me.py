from datetime import date
from typing import Any
from httpx import AsyncClient
import pytest
from fastapi import status

from app.models.userprofile import UserGender
from tests.integral.conftest import TEST_BASE_URL, TestArtist, TestUser, auth_headers


@pytest.mark.asyncio
class TestUpdateCurrentUser:
    """Tests for the PUT /me endpoint."""

    async def test_update_profile_full_update(self, async_client: AsyncClient, test_listener_full: TestUser) -> None:
        """Successfully update the authenticated user's profile."""
        update_data: dict[str, str] = {
            "username": "new_username",
            "full_name": "New Full Name",
            "birthdate": date(2025, 12, 31).isoformat(),
            "gender": UserGender.PREFER_NOT_TO_SAY,
            "phone_number": "+9876543210",
            "address": "New Address",
            "bio": "New Bio"
        }

        response = await async_client.put(f"{TEST_BASE_URL}/me", headers=auth_headers(test_listener_full.id, role='listener'), json=update_data)

        assert response.status_code == status.HTTP_200_OK, \
            f"Expected status code 200, got {response.status_code}. Response: {response.text}"
    
        response_data = response.json()
        expected_data: dict[str, Any] = {
            'id': str(test_listener_full.id),
            'username': update_data['username'],
            'fullName': update_data['full_name'],
            'birthdate': update_data['birthdate'],
            'gender': update_data['gender'],
            'phoneNumber': update_data['phone_number'],
            'address': update_data['address'],
            'profilePhoto': test_listener_full.profile.profile_photo,
            'bio': update_data['bio'],
            'country': test_listener_full.account.country.value,
            'followersCount': test_listener_full.profile.followers_count,
            'followingCount': test_listener_full.profile.following_count,
        }

        for field, expected_value in expected_data.items():
            assert field in response_data, f"Field '{field}' not found in response"
            assert response_data[field] == expected_value, \
                f"Mismatch in field '{field}': expected {expected_value}, got {response_data[field]}"
    
    async def test_update_profile_partial_update(self, async_client: AsyncClient, test_artist_full: TestArtist) -> None:
        """Successfully partially update the authenticated user's profile."""
        update_data: dict[str, str] = {
            "full_name": "New Name",
        }

        response = await async_client.put(f"{TEST_BASE_URL}/me", headers=auth_headers(test_artist_full.id, role='artist'), json=update_data)

        assert response.status_code == status.HTTP_200_OK, \
            f"Expected status code 200, got {response.status_code}. Response: {response.text}"
        
        response_data = response.json()
        expected_data: dict[str, Any] = {
            'id': str(test_artist_full.id),
            'username': test_artist_full.profile.username,
            'fullName': update_data['full_name'],
            'birthdate': test_artist_full.profile.birthdate.isoformat() if test_artist_full.profile.birthdate else None,
            'gender': test_artist_full.profile.gender.value,
            'phoneNumber': test_artist_full.profile.phone_number,
            'address': test_artist_full.profile.address,
            'profilePhoto': test_artist_full.profile.profile_photo,
            'bio': test_artist_full.profile.bio,
            'country': test_artist_full.account.country.value,
            'followersCount': test_artist_full.profile.followers_count,
            'followingCount': test_artist_full.profile.following_count,
        }

        for field, expected_value in expected_data.items():
            assert field in response_data, f"Field '{field}' not found in response"
            assert response_data[field] == expected_value, \
                f"Mismatch in field '{field}': expected {expected_value}, got {response_data[field]}"
    
    async def test_update_profile_username_taken(self, async_client: AsyncClient, test_listener_full: TestUser, test_artist_full: TestArtist) -> None:
        """Fail to update profile when username is already taken."""
        update_data: dict[str, Any] = {
            "username": test_artist_full.profile.username,
        }

        response = await async_client.put(f"{TEST_BASE_URL}/me", headers=auth_headers(test_listener_full.id, role='listener'), json=update_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST, \
            f"Expected status code 400, got {response.status_code}. Response: {response.text}"
        assert response.json() == {
            "type": "about:blank",
            "title": "Bad request error",
            "status": 400,
            "detail": "El nombre de usuario ya está en uso",
            "instance": "/me"
        }
    
    async def test_update_profile_missing_required_fields(self, async_client: AsyncClient, test_listener_full: TestUser) -> None:
        """Fail to update profile when required fields are missing."""
        update_data: dict[str, str] = {
            "birthdate": "",
        }

        response = await async_client.put(f"{TEST_BASE_URL}/me", headers=auth_headers(test_listener_full.id, role='listener'), json=update_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY, \
            f"Expected status code 422, got {response.status_code}. Response: {response.text}"
