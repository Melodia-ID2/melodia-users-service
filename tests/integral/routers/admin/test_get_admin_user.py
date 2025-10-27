import uuid

import pytest
from httpx import AsyncClient
from fastapi import status
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.main import app
from tests.integral.fixtures.factories import TestArtist, TestUser
from tests.integral.conftest import TEST_BASE_URL, auth_headers

sync_engine = create_engine(settings.DATABASE_URL.replace("+asyncpg", ""))




@pytest.mark.asyncio
class TestAdminGetUser:
    async def test_get_listener_minimal(self, async_client: AsyncClient, test_listener_minimal: TestUser) -> None:
        """Return detailed info for a minimal listener profile."""
        response = await async_client.get(f"{TEST_BASE_URL}/admin/{test_listener_minimal.id}", headers=auth_headers(uuid.uuid4(), role="admin"))
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            "id": str(test_listener_minimal.id),
            "email": test_listener_minimal.credentials.email,
            "username": test_listener_minimal.profile.username,
            "role": test_listener_minimal.account.role.value,
            "status": test_listener_minimal.account.status.value,
            "fullName": test_listener_minimal.profile.full_name,
            "phoneNumber": None,
            "address": None,
            "country": test_listener_minimal.account.country,
            "birthdate": test_listener_minimal.profile.birthdate.isoformat(),
            "profilePhoto": None,
            "lastLogin": test_listener_minimal.account.last_login.isoformat() if test_listener_minimal.account.last_login else None,
            "createdAt": test_listener_minimal.account.created_at.isoformat(),
        }
        app.dependency_overrides = {}
    
    async def test_get_listener_full(self, async_client: AsyncClient, test_listener_full: TestUser) -> None:
        """Return detailed info for a complete listener profile."""
        response = await async_client.get(f"{TEST_BASE_URL}/admin/{test_listener_full.id}", headers=auth_headers(uuid.uuid4(), role="admin"))
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            "id": str(test_listener_full.id),
            "email": test_listener_full.credentials.email,
            "username": test_listener_full.profile.username,
            "role": test_listener_full.account.role.value,
            "status": test_listener_full.account.status.value,
            "fullName": test_listener_full.profile.full_name,
            "phoneNumber": test_listener_full.profile.phone_number,
            "address": test_listener_full.profile.address,
            "country": test_listener_full.account.country,
            "birthdate": test_listener_full.profile.birthdate.isoformat(),
            "profilePhoto": test_listener_full.profile.profile_photo,
            "lastLogin": test_listener_full.account.last_login.isoformat() if test_listener_full.account.last_login else None,
            "createdAt": test_listener_full.account.created_at.isoformat(),
        }
        app.dependency_overrides = {}

    async def test_get_artist(self, async_client: AsyncClient, test_artist_full: TestArtist) -> None:
        """Return detailed info for an artist profile including role as artist."""
        response = await async_client.get(f"{TEST_BASE_URL}/admin/{test_artist_full.id}", headers=auth_headers(uuid.uuid4(), role="admin"))
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["role"] == "artist"

    async def test_get_nonexistent_account(self, async_client: AsyncClient) -> None:
        """Return 404 when the user account does not exist."""
        non_existent_user_id = uuid.UUID(int=0)

        response = await async_client.get(f"{TEST_BASE_URL}/admin/{non_existent_user_id}", headers=auth_headers(uuid.uuid4(), role="admin"))
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json() == {
            "detail": f"Cuenta de usuario con id: {non_existent_user_id} no encontrada",
            "instance": f"/admin/{non_existent_user_id}",
            "status": status.HTTP_404_NOT_FOUND,
            "title": "Resource Not Found",
            "type": "about:blank"
        }

    async def test_get_nonexistent_profile(self, async_client: AsyncClient, test_listener_minimal: TestUser, session: AsyncSession) -> None:
        """Return 404 when the user profile does not exist for an existing account."""
        await session.delete(test_listener_minimal.profile)
        await session.commit()
        
        response = await async_client.get(f"{TEST_BASE_URL}/admin/{test_listener_minimal.id}", headers=auth_headers(uuid.uuid4(), role="admin"))
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json() == {
            "detail": f"Perfil de usuario con id: {test_listener_minimal.id} no encontrado",
            "instance": f"/admin/{test_listener_minimal.id}",
            "status": status.HTTP_404_NOT_FOUND,
            "title": "Resource Not Found",
            "type": "about:blank"
        }