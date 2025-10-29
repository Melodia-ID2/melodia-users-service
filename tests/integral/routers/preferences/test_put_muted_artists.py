import uuid
import pytest
from httpx import AsyncClient
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.user_muted_artist import UserMutedArtist
from tests.integral.conftest import TEST_BASE_URL, TestUser, auth_headers
from tests.integral.routers.preferences.helpers import expected_error_response


async def is_artist_muted(session: AsyncSession, user_id: uuid.UUID, artist_id: uuid.UUID) -> bool:
    """Helper to check if an artist is muted by a user."""
    result = await session.execute(
        select(UserMutedArtist).where(
            UserMutedArtist.user_id == user_id,
            UserMutedArtist.artist_id == artist_id
        )
    )
    return result.scalar_one_or_none() is not None


async def add_muted_artist(session: AsyncSession, user_id: uuid.UUID, artist_id: uuid.UUID) -> None:
    """Helper to add a muted artist to the database."""
    muted = UserMutedArtist(user_id=user_id, artist_id=artist_id)
    session.add(muted)
    await session.commit()


@pytest.mark.asyncio
class TestPutMutedArtists:
    """Tests for the PUT /preferences/notifications/muted-artists/{artist_id} endpoint."""

    async def test_put_muted_artist_success(
        self, async_client: AsyncClient, test_listener_full: TestUser, test_artist_full: TestUser, session: AsyncSession
    ) -> None:
        """Successfully mute an artist."""
        response = await async_client.put(
            f"{TEST_BASE_URL}/preferences/notifications/muted-artists/{test_artist_full.id}",
            headers=auth_headers(test_listener_full.id, role="listener"),
        )

        assert response.status_code == status.HTTP_200_OK, \
            f"Expected status code 200, got {response.status_code}. Response: {response.text}"
        assert response.json() == {"artistId": str(test_artist_full.id)}

        assert await is_artist_muted(session, test_listener_full.id, test_artist_full.id)

    async def test_put_muted_artist_idempotent(
        self, async_client: AsyncClient, test_listener_full: TestUser, test_artist_full: TestUser, session: AsyncSession
    ) -> None:
        """Muting the same artist twice is idempotent."""
        response1 = await async_client.put(
            f"{TEST_BASE_URL}/preferences/notifications/muted-artists/{test_artist_full.id}",
            headers=auth_headers(test_listener_full.id, role="listener"),
        )
        assert response1.status_code == status.HTTP_200_OK
        assert response1.json() == {"artistId": str(test_artist_full.id)}

        response2 = await async_client.put(
            f"{TEST_BASE_URL}/preferences/notifications/muted-artists/{test_artist_full.id}",
            headers=auth_headers(test_listener_full.id, role="listener"),
        )
        assert response2.status_code == status.HTTP_200_OK
        assert response2.json() == {"artistId": str(test_artist_full.id)}

        result = await session.execute(
            select(UserMutedArtist).where(
                UserMutedArtist.user_id == test_listener_full.id,
                UserMutedArtist.artist_id == test_artist_full.id
            )
        )
        records = result.scalars().all()
        assert len(records) == 1

    async def test_put_muted_artist_for_artist_user(
        self, async_client: AsyncClient, test_artist_full: TestUser, test_artist_minimal: TestUser, session: AsyncSession
    ) -> None:
        """Artists can also mute other artists."""
        response = await async_client.put(
            f"{TEST_BASE_URL}/preferences/notifications/muted-artists/{test_artist_minimal.id}",
            headers=auth_headers(test_artist_full.id, role="artist"),
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"artistId": str(test_artist_minimal.id)}
        assert await is_artist_muted(session, test_artist_full.id, test_artist_minimal.id)

    async def test_put_muted_artist_multiple_different_artists(
        self, 
        async_client: AsyncClient, 
        test_listener_full: TestUser, 
        test_artist_full: TestUser,
        test_artist_minimal: TestUser,
        session: AsyncSession
    ) -> None:
        """Can mute multiple different artists."""
        response1 = await async_client.put(
            f"{TEST_BASE_URL}/preferences/notifications/muted-artists/{test_artist_full.id}",
            headers=auth_headers(test_listener_full.id, role="listener"),
        )
        assert response1.status_code == status.HTTP_200_OK

        response2 = await async_client.put(
            f"{TEST_BASE_URL}/preferences/notifications/muted-artists/{test_artist_minimal.id}",
            headers=auth_headers(test_listener_full.id, role="listener"),
        )
        assert response2.status_code == status.HTTP_200_OK

        assert await is_artist_muted(session, test_listener_full.id, test_artist_full.id)
        assert await is_artist_muted(session, test_listener_full.id, test_artist_minimal.id)

    async def test_put_muted_artist_nonexistent_artist(
        self, async_client: AsyncClient, test_listener_full: TestUser
    ) -> None:
        """Attempting to mute a nonexistent artist fails."""
        nonexistent_artist_id = uuid.uuid4()
        response = await async_client.put(
            f"{TEST_BASE_URL}/preferences/notifications/muted-artists/{nonexistent_artist_id}",
            headers=auth_headers(test_listener_full.id, role="listener"),
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json() == expected_error_response(
            404,
            "Artista no encontrado",
            f"/preferences/notifications/muted-artists/{nonexistent_artist_id}"
        )

    async def test_put_muted_artist_non_artist_role(
        self, async_client: AsyncClient, test_listener_full: TestUser, test_listener_minimal: TestUser
    ) -> None:
        """Attempting to mute a user who is not an artist fails (if role validation is enforced)."""
        response = await async_client.put(
            f"{TEST_BASE_URL}/preferences/notifications/muted-artists/{test_listener_minimal.id}",
            headers=auth_headers(test_listener_full.id, role="listener"),
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json() == expected_error_response(
            404,
            "Artista no encontrado",
            f"/preferences/notifications/muted-artists/{test_listener_minimal.id}"
        )

    async def test_put_muted_artist_unauthenticated(self, async_client: AsyncClient, test_artist_full: TestUser) -> None:
        """Attempting to mute an artist without authentication fails."""
        response = await async_client.put(
            f"{TEST_BASE_URL}/preferences/notifications/muted-artists/{test_artist_full.id}"
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json() == expected_error_response(
            401,
            "Token de autenticación invalido o no proporcionado",
            f"/preferences/notifications/muted-artists/{test_artist_full.id}"
        )

    async def test_put_muted_artist_nonexistent_user(self, async_client: AsyncClient, test_artist_full: TestUser) -> None:
        """Attempting to mute an artist for a nonexistent user fails."""
        nonexistent_user_id = uuid.uuid4()
        response = await async_client.put(
            f"{TEST_BASE_URL}/preferences/notifications/muted-artists/{test_artist_full.id}",
            headers=auth_headers(nonexistent_user_id, role="listener"),
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json() == expected_error_response(
            404,
            "Usuario no encontrado",
            f"/preferences/notifications/muted-artists/{test_artist_full.id}"
        )

    async def test_put_muted_artist_invalid_uuid(
        self, async_client: AsyncClient, test_listener_full: TestUser
    ) -> None:
        """Attempting to mute with invalid UUID fails."""
        response = await async_client.put(
            f"{TEST_BASE_URL}/preferences/notifications/muted-artists/invalid-uuid",
            headers=auth_headers(test_listener_full.id, role="listener"),
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_put_muted_artist_isolation_between_users(
        self,
        async_client: AsyncClient,
        test_listener_full: TestUser,
        test_listener_minimal: TestUser,
        test_artist_full: TestUser,
        session: AsyncSession
    ) -> None:
        """Muting is isolated between users."""
        response = await async_client.put(
            f"{TEST_BASE_URL}/preferences/notifications/muted-artists/{test_artist_full.id}",
            headers=auth_headers(test_listener_full.id, role="listener"),
        )
        assert response.status_code == status.HTTP_200_OK
        assert await is_artist_muted(session, test_listener_full.id, test_artist_full.id)
        assert not await is_artist_muted(session, test_listener_minimal.id, test_artist_full.id)
