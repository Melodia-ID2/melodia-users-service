from typing import Any
from httpx import AsyncClient
from fastapi import status
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from tests.integral.fixtures.auth import auth_headers
from tests.integral.fixtures.factories import TestUser
from tests.integral.fixtures.server import TEST_BASE_URL

@pytest.mark.asyncio
class TestPostUserProfile:
    """Tests for the POST /me endpoint."""

    async def test_create_profile_full(self, async_client: AsyncClient, test_listener_full: TestUser, session: AsyncSession) -> None:
        """Successfully create a user profile with full data."""
        await session.delete(test_listener_full.profile)
        await session.commit()

        user_profile = test_listener_full.profile
        payload = user_profile.model_dump(mode='json')
        payload.pop("id", None)
        response = await async_client.post(f"{TEST_BASE_URL}/me", headers=auth_headers(test_listener_full.id, 'listener'), json=payload)

        assert response.status_code == status.HTTP_201_CREATED, \
            f"Expected status code 201, got {response.status_code}. Response: {response.text}"
        
        response_data = response.json()
        expected_data: dict[str, Any] = {
            'id': str(test_listener_full.id),
            'username': user_profile.username,
            'fullName': user_profile.full_name,
            'birthdate': user_profile.birthdate.isoformat(),
            'gender': user_profile.gender.value,
            'phoneNumber': user_profile.phone_number,
            'address': user_profile.address,
            'profilePhoto': user_profile.profile_photo,
            'bio': user_profile.bio,
            'followersCount': user_profile.followers_count,
            'followingCount': user_profile.following_count,
            'preferences': test_listener_full.account.preferences
        }

        for field, expected_value in expected_data.items():
            assert field in response_data, f"Field '{field}' not found in response"
            assert response_data[field] == expected_value, \
                f"Mismatch in field '{field}': expected {expected_value}, got {response_data[field]}"
    
    async def test_create_profile_minimal(self, async_client: AsyncClient, test_listener_minimal: TestUser, session: AsyncSession) -> None:
        """Successfully create a user profile with minimal data."""
        await session.delete(test_listener_minimal.profile)
        await session.commit()

        user_profile = test_listener_minimal.profile
        payload = user_profile.model_dump(mode='json')
        payload.pop("id", None)
        response = await async_client.post(f"{TEST_BASE_URL}/me", headers=auth_headers(test_listener_minimal.id, 'listener'), json=payload)

        assert response.status_code == status.HTTP_201_CREATED, \
            f"Expected status code 201, got {response.status_code}. Response: {response.text}"
        
        response_data = response.json()
        expected_data: dict[str, Any] = {
            'id': str(test_listener_minimal.id),
            'username': user_profile.username,
            'fullName': user_profile.full_name,
            'birthdate': user_profile.birthdate.isoformat(),
            'gender': user_profile.gender,
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
    
    async def test_create_profile_profile_already_exists(self, async_client: AsyncClient, test_listener_full: TestUser) -> None:
        """Attempt to create a profile when one already exists."""
        user_profile = test_listener_full.profile
        payload = user_profile.model_dump(mode='json')
        payload.pop("id", None)
        response = await async_client.post(f"{TEST_BASE_URL}/me", headers=auth_headers(test_listener_full.id, 'listener'), json=payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST, \
            f"Expected status code 400, got {response.status_code}. Response: {response.text}"
        
        assert response.json() == {
            "detail": "El perfil ya existe",
            "instance": "/me",
            "status": status.HTTP_400_BAD_REQUEST,
            "title": "Bad request error",
            "type": "about:blank"
        }
    
    async def test_create_profile_username_taken(self, async_client: AsyncClient, test_listener_full: TestUser, test_artist_full: TestUser, session: AsyncSession) -> None:
        """Attempt to create a profile with a username that is already taken."""
        await session.delete(test_listener_full.profile)
        await session.commit()

        user_profile = test_listener_full.profile
        payload = user_profile.model_dump(mode='json')
        payload.pop("id", None)
        payload["username"] = test_artist_full.profile.username
        response = await async_client.post(f"{TEST_BASE_URL}/me", headers=auth_headers(test_listener_full.id, 'listener'), json=payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST, \
            f"Expected status code 400, got {response.status_code}. Response: {response.text}"
        
        assert response.json() == {
            "detail": "El nombre de usuario ya está en uso",
            "instance": "/me",
            "status": status.HTTP_400_BAD_REQUEST,
            "title": "Bad request error",
            "type": "about:blank"
        }