import uuid
import pytest
from httpx import AsyncClient
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_muted_artist import UserMutedArtist
from tests.integral.conftest import TEST_BASE_URL, TestUser, auth_headers
from tests.integral.routers.preferences.helpers import expected_error_response


async def add_muted_artist(session: AsyncSession, user_id: uuid.UUID, artist_id: uuid.UUID) -> None:
    """Helper to add a muted artist to the database."""
    muted = UserMutedArtist(user_id=user_id, artist_id=artist_id)
    session.add(muted)
    await session.commit()


@pytest.mark.asyncio
class TestGetMutedArtists:
    """Tests for the GET /preferences/notifications/muted-artists endpoint."""

    async def test_get_muted_artists_empty_list(
        self, async_client: AsyncClient, test_listener_full: TestUser
    ) -> None:
        """Successfully retrieve empty list when no artists are muted."""
        response = await async_client.get(
            f"{TEST_BASE_URL}/preferences/notifications/muted-artists",
            headers=auth_headers(test_listener_full.id, role="listener"),
        )

        assert response.status_code == status.HTTP_200_OK, \
            f"Expected status code 200, got {response.status_code}. Response: {response.text}"
        assert response.json() == {"mutedArtists": []}

    async def test_get_muted_artists_with_one_artist(
        self, async_client: AsyncClient, test_listener_full: TestUser, test_artist_full: TestUser, session: AsyncSession
    ) -> None:
        """Successfully retrieve list with one muted artist."""
        await add_muted_artist(session, test_listener_full.id, test_artist_full.id)

        response = await async_client.get(
            f"{TEST_BASE_URL}/preferences/notifications/muted-artists",
            headers=auth_headers(test_listener_full.id, role="listener"),
        )

        assert response.status_code == status.HTTP_200_OK, \
            f"Expected status code 200, got {response.status_code}. Response: {response.text}"
        data = response.json()
        assert "mutedArtists" in data
        assert len(data["mutedArtists"]) == 1
        assert data["mutedArtists"][0] == str(test_artist_full.id)

    async def test_get_muted_artists_with_multiple_artists(
        self, 
        async_client: AsyncClient, 
        test_listener_full: TestUser, 
        test_artist_full: TestUser,
        test_artist_minimal: TestUser,
        session: AsyncSession
    ) -> None:
        """Successfully retrieve list with multiple muted artists."""
        await add_muted_artist(session, test_listener_full.id, test_artist_full.id)
        await add_muted_artist(session, test_listener_full.id, test_artist_minimal.id)

        response = await async_client.get(
            f"{TEST_BASE_URL}/preferences/notifications/muted-artists",
            headers=auth_headers(test_listener_full.id, role="listener"),
        )

        assert response.status_code == status.HTTP_200_OK, \
            f"Expected status code 200, got {response.status_code}. Response: {response.text}"
        data = response.json()
        assert "mutedArtists" in data
        assert len(data["mutedArtists"]) == 2
        muted_ids = {uuid.UUID(artist_id) for artist_id in data["mutedArtists"]}
        assert test_artist_full.id in muted_ids
        assert test_artist_minimal.id in muted_ids

    async def test_get_muted_artists_for_artist_user(
        self, async_client: AsyncClient, test_artist_full: TestUser, test_artist_minimal: TestUser, session: AsyncSession
    ) -> None:
        """Artists can also retrieve their muted artists list."""
        await add_muted_artist(session, test_artist_full.id, test_artist_minimal.id)

        response = await async_client.get(
            f"{TEST_BASE_URL}/preferences/notifications/muted-artists",
            headers=auth_headers(test_artist_full.id, role="artist"),
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["mutedArtists"]) == 1
        assert data["mutedArtists"][0] == str(test_artist_minimal.id)

    async def test_get_muted_artists_unauthenticated(self, async_client: AsyncClient) -> None:
        """Attempting to retrieve muted artists without authentication fails."""
        response = await async_client.get(
            f"{TEST_BASE_URL}/preferences/notifications/muted-artists"
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json() == expected_error_response(
            401,
            "Token de autenticación invalido o no proporcionado",
            "/preferences/notifications/muted-artists"
        )

    async def test_get_muted_artists_nonexistent_user(self, async_client: AsyncClient) -> None:
        """Attempting to retrieve muted artists for a nonexistent user fails."""
        nonexistent_user_id = uuid.uuid4()
        response = await async_client.get(
            f"{TEST_BASE_URL}/preferences/notifications/muted-artists",
            headers=auth_headers(nonexistent_user_id, role="listener"),
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json() == expected_error_response(
            404,
            "Usuario no encontrado",
            "/preferences/notifications/muted-artists"
        )

    async def test_get_muted_artists_isolation_between_users(
        self,
        async_client: AsyncClient,
        test_listener_full: TestUser,
        test_listener_minimal: TestUser,
        test_artist_full: TestUser,
        session: AsyncSession
    ) -> None:
        """Each user's muted artists list is independent."""
        await add_muted_artist(session, test_listener_full.id, test_artist_full.id)

        response = await async_client.get(
            f"{TEST_BASE_URL}/preferences/notifications/muted-artists",
            headers=auth_headers(test_listener_minimal.id, role="listener"),
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"mutedArtists": []}

        response = await async_client.get(
            f"{TEST_BASE_URL}/preferences/notifications/muted-artists",
            headers=auth_headers(test_listener_full.id, role="listener"),
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["mutedArtists"]) == 1
        assert data["mutedArtists"][0] == str(test_artist_full.id)
