import pytest
from httpx import AsyncClient
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.userprofile import UserFollows
from tests.integral.fixtures.auth import auth_headers
from tests.integral.fixtures.factories import TestArtist, TestUser
from tests.integral.fixtures.server import TEST_BASE_URL


@pytest.mark.asyncio
class TestGetFollowers:
    """Tests for the GET /{user_id}/follows endpoint."""

    async def test_get_followers_empty(self, async_client: AsyncClient, test_listener_full: TestUser) -> None:
        """Test retrieving followers when there are none."""
        response = await async_client.get(f"{TEST_BASE_URL}/{test_listener_full.id}/followers", headers=auth_headers(test_listener_full.id, role="listener"))
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            "follows": [],
        }
    
    async def test_get_followers_for_other_not_being_followed_by_current(self, async_client: AsyncClient, test_listener_full: TestUser, test_listener_minimal: TestUser, test_artist_full: TestArtist, session: AsyncSession) -> None:
        """Test retrieving followers when follower is not followed back."""
        follow_link = UserFollows(follower_id=test_listener_minimal.id, followed_id=test_listener_full.id)
        session.add(follow_link)
        await session.commit()

        response = await async_client.get(f"{TEST_BASE_URL}/{test_listener_full.id}/followers", headers=auth_headers(test_artist_full.id, role="artist"))
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            "follows": [
                {
                    "id": str(test_listener_minimal.id),
                    "username": test_listener_minimal.profile.username,
                    "profilePhoto": test_listener_minimal.profile.profile_photo,
                    "followersCount": test_listener_minimal.profile.followers_count,
                    "isFollowing": False,
                }
            ]
        }

    async def test_get_followers_for_other_being_followed_by_current(self, async_client: AsyncClient, test_listener_full: TestUser, test_listener_minimal: TestUser, test_artist_full: TestArtist, session: AsyncSession) -> None:
        """Test retrieving followers when follower is followed back."""
        follow_link_1 = UserFollows(follower_id=test_listener_minimal.id, followed_id=test_listener_full.id)
        follow_link_2 = UserFollows(follower_id=test_artist_full.id, followed_id=test_listener_minimal.id)
        session.add_all([follow_link_1, follow_link_2])
        await session.commit()

        response = await async_client.get(f"{TEST_BASE_URL}/{test_listener_full.id}/followers", headers=auth_headers(test_artist_full.id, role="artist"))
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            "follows": [
                {
                    "id": str(test_listener_minimal.id),
                    "username": test_listener_minimal.profile.username,
                    "profilePhoto": test_listener_minimal.profile.profile_photo,
                    "followersCount": test_listener_minimal.profile.followers_count,
                    "isFollowing": True,
                }
            ]
        }

@pytest.mark.asyncio
class TestGetFollowing:
    """Tests for the GET /{user_id}/follows endpoint."""
    
    async def test_get_following_empty(self, async_client: AsyncClient, test_listener_full: TestUser) -> None:
        """Test retrieving following when there are none."""
        response = await async_client.get(f"{TEST_BASE_URL}/{test_listener_full.id}/following", headers=auth_headers(test_listener_full.id, role="listener"))
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            "follows": [],
        }

    async def test_get_following_for_other_not_followed_by_current(self, async_client: AsyncClient, test_listener_full: TestUser, test_listener_minimal: TestUser, test_artist_full: TestArtist, session: AsyncSession) -> None:
        """Test retrieving following when not followed by current user."""
        follow_link = UserFollows(follower_id=test_listener_full.id, followed_id=test_listener_minimal.id)
        session.add(follow_link)
        await session.commit()

        response = await async_client.get(f"{TEST_BASE_URL}/{test_listener_full.id}/following", headers=auth_headers(test_artist_full.id, role="artist"))
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            "follows": [
                {
                    "id": str(test_listener_minimal.id),
                    "username": test_listener_minimal.profile.username,
                    "profilePhoto": test_listener_minimal.profile.profile_photo,
                    "followersCount": test_listener_minimal.profile.followers_count,
                    "isFollowing": False,
                }
            ]
        }

    async def test_get_following_for_other_followed_by_current(self, async_client: AsyncClient, test_listener_full: TestUser, test_listener_minimal: TestUser, test_artist_full: TestArtist, session: AsyncSession) -> None:
        """Test retrieving following when followed by current user."""
        follow_link_1 = UserFollows(follower_id=test_listener_full.id, followed_id=test_listener_minimal.id)
        follow_link_2 = UserFollows(follower_id=test_artist_full.id, followed_id=test_listener_minimal.id)
        session.add_all([follow_link_1, follow_link_2])
        await session.commit()

        response = await async_client.get(f"{TEST_BASE_URL}/{test_listener_full.id}/following", headers=auth_headers(test_artist_full.id, role="artist"))
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            "follows": [
                {
                    "id": str(test_listener_minimal.id),
                    "username": test_listener_minimal.profile.username,
                    "profilePhoto": test_listener_minimal.profile.profile_photo,
                    "followersCount": test_listener_minimal.profile.followers_count,
                    "isFollowing": True,
                }
            ]
        }

    async def test_get_following_filter_artist_only(
        self,
        async_client: AsyncClient,
        test_listener_full: TestUser,
        test_listener_minimal: TestUser,
        test_artist_minimal: TestUser,
        test_artist_full: TestArtist,
        session: AsyncSession,
    ) -> None:
        """Filter following list by type=artist should return only artists."""
        follow_link_1 = UserFollows(follower_id=test_listener_full.id, followed_id=test_listener_minimal.id)  # listener
        follow_link_2 = UserFollows(follower_id=test_listener_full.id, followed_id=test_artist_minimal.id)   # artist
        session.add_all([follow_link_1, follow_link_2])
        await session.commit()

        response = await async_client.get(
            f"{TEST_BASE_URL}/{test_listener_full.id}/following",
            params={"type": "artist"},
            headers=auth_headers(test_artist_full.id, role="artist"),
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            "follows": [
                {
                    "id": str(test_artist_minimal.id),
                    "username": test_artist_minimal.profile.username,
                    "profilePhoto": test_artist_minimal.profile.profile_photo,
                    "followersCount": test_artist_minimal.profile.followers_count,
                    "isFollowing": False,
                }
            ]
        }

    async def test_get_following_filter_listener_only(
        self,
        async_client: AsyncClient,
        test_listener_full: TestUser,
        test_listener_minimal: TestUser,
        test_artist_minimal: TestUser,
        test_artist_full: TestArtist,
        session: AsyncSession,
    ) -> None:
        """Filter following list by type=listener should return only listeners."""
        follow_link_1 = UserFollows(follower_id=test_listener_full.id, followed_id=test_listener_minimal.id)  # listener
        follow_link_2 = UserFollows(follower_id=test_listener_full.id, followed_id=test_artist_minimal.id)   # artist
        session.add_all([follow_link_1, follow_link_2])
        await session.commit()

        response = await async_client.get(
            f"{TEST_BASE_URL}/{test_listener_full.id}/following",
            params={"type": "listener"},
            headers=auth_headers(test_artist_full.id, role="artist"),
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            "follows": [
                {
                    "id": str(test_listener_minimal.id),
                    "username": test_listener_minimal.profile.username,
                    "profilePhoto": test_listener_minimal.profile.profile_photo,
                    "followersCount": test_listener_minimal.profile.followers_count,
                    "isFollowing": False,
                }
            ]
        }

    async def test_get_following_filter_invalid_type(
        self,
        async_client: AsyncClient,
        test_listener_full: TestUser,
        test_artist_full: TestArtist,
    ) -> None:
        """Invalid type value should return 422 Unprocessable Entity."""
        response = await async_client.get(
            f"{TEST_BASE_URL}/{test_listener_full.id}/following",
            params={"type": "band"},
            headers=auth_headers(test_artist_full.id, role="artist"),
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY