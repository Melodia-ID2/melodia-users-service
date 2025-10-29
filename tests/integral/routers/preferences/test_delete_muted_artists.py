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
    result = await session.execute(
        select(UserMutedArtist).where(
            UserMutedArtist.user_id == user_id,
            UserMutedArtist.artist_id == artist_id
        )
    )
    return result.scalar_one_or_none() is not None


async def add_muted_artist(session: AsyncSession, user_id: uuid.UUID, artist_id: uuid.UUID) -> None:
    muted = UserMutedArtist(user_id=user_id, artist_id=artist_id)
    session.add(muted)
    await session.commit()


@pytest.mark.asyncio
class TestDeleteMutedArtists:
    """Tests for the DELETE /preferences/notifications/muted-artists/{artist_id} endpoint."""

    async def test_delete_muted_artist_success(
        self, async_client: AsyncClient, test_listener_full: TestUser, test_artist_full: TestUser, session: AsyncSession
    ) -> None:
        """Successfully unmute an artist."""
        await add_muted_artist(session, test_listener_full.id, test_artist_full.id)
        assert await is_artist_muted(session, test_listener_full.id, test_artist_full.id)

        response = await async_client.delete(
            f"{TEST_BASE_URL}/preferences/notifications/muted-artists/{test_artist_full.id}",
            headers=auth_headers(test_listener_full.id, role="listener"),
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT, \
            f"Expected status code 204, got {response.status_code}. Response: {response.text}"
        assert response.text == ""

        assert not await is_artist_muted(session, test_listener_full.id, test_artist_full.id)

    async def test_delete_muted_artist_idempotent(
        self, async_client: AsyncClient, test_listener_full: TestUser, test_artist_full: TestUser, session: AsyncSession
    ) -> None:
        """Unmuting an artist that is not muted is idempotent (returns 204)."""
        assert not await is_artist_muted(session, test_listener_full.id, test_artist_full.id)

        response = await async_client.delete(
            f"{TEST_BASE_URL}/preferences/notifications/muted-artists/{test_artist_full.id}",
            headers=auth_headers(test_listener_full.id, role="listener"),
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT, \
            f"Expected status code 204, got {response.status_code}. Response: {response.text}"
        assert response.text == ""

    async def test_delete_muted_artist_twice(
        self, async_client: AsyncClient, test_listener_full: TestUser, test_artist_full: TestUser, session: AsyncSession
    ) -> None:
        """Deleting twice is idempotent."""
        await add_muted_artist(session, test_listener_full.id, test_artist_full.id)

        response1 = await async_client.delete(
            f"{TEST_BASE_URL}/preferences/notifications/muted-artists/{test_artist_full.id}",
            headers=auth_headers(test_listener_full.id, role="listener"),
        )
        assert response1.status_code == status.HTTP_204_NO_CONTENT

        response2 = await async_client.delete(
            f"{TEST_BASE_URL}/preferences/notifications/muted-artists/{test_artist_full.id}",
            headers=auth_headers(test_listener_full.id, role="listener"),
        )
        assert response2.status_code == status.HTTP_204_NO_CONTENT

        assert not await is_artist_muted(session, test_listener_full.id, test_artist_full.id)

    async def test_delete_muted_artist_for_artist_user(
        self, async_client: AsyncClient, test_artist_full: TestUser, test_artist_minimal: TestUser, session: AsyncSession
    ) -> None:
        """Artists can also unmute other artists."""
        await add_muted_artist(session, test_artist_full.id, test_artist_minimal.id)

        response = await async_client.delete(
            f"{TEST_BASE_URL}/preferences/notifications/muted-artists/{test_artist_minimal.id}",
            headers=auth_headers(test_artist_full.id, role="artist"),
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not await is_artist_muted(session, test_artist_full.id, test_artist_minimal.id)

    async def test_delete_muted_artist_preserves_other_muted_artists(
        self,
        async_client: AsyncClient,
        test_listener_full: TestUser,
        test_artist_full: TestUser,
        test_artist_minimal: TestUser,
        session: AsyncSession
    ) -> None:
        """Deleting one muted artist doesn't affect others."""
        await add_muted_artist(session, test_listener_full.id, test_artist_full.id)
        await add_muted_artist(session, test_listener_full.id, test_artist_minimal.id)

        response = await async_client.delete(
            f"{TEST_BASE_URL}/preferences/notifications/muted-artists/{test_artist_full.id}",
            headers=auth_headers(test_listener_full.id, role="listener"),
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT

        assert not await is_artist_muted(session, test_listener_full.id, test_artist_full.id)

        assert await is_artist_muted(session, test_listener_full.id, test_artist_minimal.id)

    async def test_delete_muted_artist_nonexistent_artist(
        self, async_client: AsyncClient, test_listener_full: TestUser
    ) -> None:
        """Attempting to unmute a nonexistent artist fails with 404."""
        nonexistent_artist_id = uuid.uuid4()
        response = await async_client.delete(
            f"{TEST_BASE_URL}/preferences/notifications/muted-artists/{nonexistent_artist_id}",
            headers=auth_headers(test_listener_full.id, role="listener"),
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json() == expected_error_response(
            404,
            "Artista no encontrado",
            f"/preferences/notifications/muted-artists/{nonexistent_artist_id}"
        )

    async def test_delete_muted_artist_non_artist_role(
        self, async_client: AsyncClient, test_listener_full: TestUser, test_listener_minimal: TestUser
    ) -> None:
        """Attempting to unmute a user who is not an artist fails (if role validation is enforced)."""
        response = await async_client.delete(
            f"{TEST_BASE_URL}/preferences/notifications/muted-artists/{test_listener_minimal.id}",
            headers=auth_headers(test_listener_full.id, role="listener"),
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json() == expected_error_response(
            404,
            "Artista no encontrado",
            f"/preferences/notifications/muted-artists/{test_listener_minimal.id}"
        )

    async def test_delete_muted_artist_unauthenticated(self, async_client: AsyncClient, test_artist_full: TestUser) -> None:
        """Attempting to unmute an artist without authentication fails."""
        response = await async_client.delete(
            f"{TEST_BASE_URL}/preferences/notifications/muted-artists/{test_artist_full.id}"
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json() == expected_error_response(
            401,
            "Token de autenticación invalido o no proporcionado",
            f"/preferences/notifications/muted-artists/{test_artist_full.id}"
        )

    async def test_delete_muted_artist_nonexistent_user(self, async_client: AsyncClient, test_artist_full: TestUser) -> None:
        """Attempting to unmute an artist for a nonexistent user fails."""
        nonexistent_user_id = uuid.uuid4()
        response = await async_client.delete(
            f"{TEST_BASE_URL}/preferences/notifications/muted-artists/{test_artist_full.id}",
            headers=auth_headers(nonexistent_user_id, role="listener"),
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json() == expected_error_response(
            404,
            "Usuario no encontrado",
            f"/preferences/notifications/muted-artists/{test_artist_full.id}"
        )

    async def test_delete_muted_artist_invalid_uuid(
        self, async_client: AsyncClient, test_listener_full: TestUser
    ) -> None:
        """Attempting to unmute with invalid UUID fails."""
        response = await async_client.delete(
            f"{TEST_BASE_URL}/preferences/notifications/muted-artists/invalid-uuid",
            headers=auth_headers(test_listener_full.id, role="listener"),
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_delete_muted_artist_isolation_between_users(
        self,
        async_client: AsyncClient,
        test_listener_full: TestUser,
        test_listener_minimal: TestUser,
        test_artist_full: TestUser,
        session: AsyncSession
    ) -> None:
        """Unmuting is isolated between users."""
        await add_muted_artist(session, test_listener_full.id, test_artist_full.id)
        await add_muted_artist(session, test_listener_minimal.id, test_artist_full.id)

        response = await async_client.delete(
            f"{TEST_BASE_URL}/preferences/notifications/muted-artists/{test_artist_full.id}",
            headers=auth_headers(test_listener_full.id, role="listener"),
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT

        assert not await is_artist_muted(session, test_listener_full.id, test_artist_full.id)
        assert await is_artist_muted(session, test_listener_minimal.id, test_artist_full.id)

    async def test_delete_muted_artist_cascade_on_user_delete(
        self,
        async_client: AsyncClient,
        test_listener_full: TestUser,
        test_artist_full: TestUser,
        session: AsyncSession
    ) -> None:
        """Muted artists are deleted when the user is deleted (CASCADE behavior)."""
        await add_muted_artist(session, test_listener_full.id, test_artist_full.id)
        assert await is_artist_muted(session, test_listener_full.id, test_artist_full.id)

        result = await session.execute(
            select(UserMutedArtist).where(UserMutedArtist.user_id == test_listener_full.id)
        )
        muted_records = result.scalars().all()
        assert len(muted_records) == 1

        from app.models.useraccount import UserAccount
        result = await session.execute(select(UserAccount).where(UserAccount.id == test_listener_full.id))
        account = result.scalar_one()
        await session.delete(account)
        await session.commit()

        result = await session.execute(
            select(UserMutedArtist).where(UserMutedArtist.user_id == test_listener_full.id)
        )
        muted_records = result.scalars().all()
        assert len(muted_records) == 0
