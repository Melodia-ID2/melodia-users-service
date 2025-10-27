import uuid
import pytest
from httpx import AsyncClient
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.userprofile import UserFollows
from tests.integral.fixtures.auth import auth_headers
from tests.integral.fixtures.factories import TestUser
from tests.integral.fixtures.server import TEST_BASE_URL


@pytest.mark.asyncio
class TestPutFollow:
    """Tests for the PUT /me/following/{user_id} endpoint."""

    async def test_put_follow_not_following(self, async_client: AsyncClient, test_listener_full: TestUser, test_listener_minimal: TestUser, session: AsyncSession) -> None:
        """Following a user who is not already being followed follows them."""
        response = await async_client.put(f"{TEST_BASE_URL}/me/following/{test_listener_minimal.id}", headers=auth_headers(test_listener_full.id, role="listener"))
        assert response.status_code == status.HTTP_200_OK

        follows = await session.execute(select(UserFollows).filter_by(follower_id=test_listener_full.id, followed_id=test_listener_minimal.id))
        assert follows.scalar() is not None
        assert response.json() == {
            "message": f"Ahora sigues a {test_listener_minimal.profile.username}",
        }

    async def test_put_follow_already_following(self, async_client: AsyncClient, test_listener_full: TestUser, test_listener_minimal: TestUser, session: AsyncSession) -> None:
        """Following a user who is already followed unfollows them."""
        follow_link = UserFollows(follower_id=test_listener_full.id, followed_id=test_listener_minimal.id)
        session.add(follow_link)
        await session.commit()

        response = await async_client.put(f"{TEST_BASE_URL}/me/following/{test_listener_minimal.id}", headers=auth_headers(test_listener_full.id, role="listener"))
        assert response.status_code == status.HTTP_200_OK

        follows = await session.execute(select(UserFollows).filter_by(follower_id=test_listener_full.id, followed_id=test_listener_minimal.id))
        assert follows.scalar() is None
        assert response.json() == {
            "message": f"Dejaste de seguir a {test_listener_minimal.profile.username}",
        }

    async def test_put_follow_self(self, async_client: AsyncClient, test_listener_full: TestUser) -> None:
        """A user cannot follow themselves."""
        response = await async_client.put(f"{TEST_BASE_URL}/me/following/{test_listener_full.id}", headers=auth_headers(test_listener_full.id, role="listener"))
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            "detail": "No puedes seguirte a ti mismo.",
            "instance": f"/me/following/{test_listener_full.id}",
            "status": status.HTTP_400_BAD_REQUEST,
            "title": "Bad request error",
            "type": "about:blank",
        }
    
    async def test_put_follow_nonexistent_user(self, async_client: AsyncClient, test_listener_full: TestUser) -> None:
        """Following a nonexistent user returns a 404 error."""
        nonexistent_user_id = uuid.UUID("00000000-0000-0000-0000-000000000000")
        response = await async_client.put(f"{TEST_BASE_URL}/me/following/{nonexistent_user_id}", headers=auth_headers(test_listener_full.id, role="listener"))
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json() == {
            "detail": "Usuario a seguir no encontrado",
            "instance": f"/me/following/{nonexistent_user_id}",
            "status": status.HTTP_404_NOT_FOUND,
            "title": "Resource Not Found",
            "type": "about:blank",
        }