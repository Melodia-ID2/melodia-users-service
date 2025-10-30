import uuid
import pytest
from httpx import AsyncClient
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date

from app.models.metricevent import MetricEvent, EventType
from app.models.useraccount import UserAccount, UserRole, UserStatus
from app.models.userprofile import UserProfile
from tests.integral.conftest import TEST_BASE_URL, TestArtist, TestUser, auth_headers


def _make_artist(session: AsyncSession, username: str) -> uuid.UUID:
    """Create and persist a simple artist account/profile. Returns user id."""
    uid = uuid.uuid4()
    session.add(UserAccount(id=uid, role=UserRole.ARTIST, status=UserStatus.ACTIVE))
    session.add(UserProfile(id=uid, username=username, full_name="Test Artist", birthdate=date(1990, 1, 1)))
    return uid


async def _seed_popularity(session: AsyncSession, artist_id: uuid.UUID, plays: int) -> None:
    """Insert `plays` MetricEvent rows for the artist popularity target."""
    for _ in range(plays):
        session.add(MetricEvent(event_type=EventType.PLAY_SONG, target_user_id=artist_id))
    await session.commit()


@pytest.mark.asyncio
class TestGetArtists:
    async def test_shape_and_minimal_fields(
        self,
        async_client: AsyncClient,
        session: AsyncSession,
        test_artist_full: TestArtist,
        test_artist_minimal: TestUser,
    ) -> None:
        """Basic shape: keys and minimal fields for each item."""
        response = await async_client.get(
            f"{TEST_BASE_URL}/artist",
            params={"page": 1, "pageSize": 10},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert set(data.keys()) == {"artists", "total", "page", "pageSize", "totalPages"}
        assert data["page"] == 1
        assert data["pageSize"] == 10
        assert data["total"] >= 2
        assert isinstance(data["totalPages"], int)
        for item in data["artists"]:
            assert set(item.keys()) == {"id", "username", "profilePhoto"}

    async def test_ordered_by_popularity_desc(
        self,
        async_client: AsyncClient,
        session: AsyncSession,
        test_artist_full: TestArtist,
        test_artist_minimal: TestUser,
        test_listener_full: TestUser,
    ) -> None:
        """Artists should be returned ordered by play_count desc, then username asc."""
        extra_id = _make_artist(session, username="gamma")
        await session.commit()

        await _seed_popularity(session, test_artist_full.id, plays=7)
        await _seed_popularity(session, test_artist_minimal.id, plays=3)
        await _seed_popularity(session, extra_id, plays=0)

        response = await async_client.get(
            f"{TEST_BASE_URL}/artist",
            params={"page": 1, "pageSize": 10},
            headers=auth_headers(test_listener_full.id, role="listener"),
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert set(data.keys()) == {"artists", "total", "page", "pageSize", "totalPages"}
        assert data["total"] == 3
        assert data["page"] == 1
        assert data["pageSize"] == 10
        ids = [item["id"] for item in data["artists"]]
        assert ids == [str(test_artist_full.id), str(test_artist_minimal.id), str(extra_id)]

    async def test_tie_breaker_username_when_same_popularity(
        self,
        async_client: AsyncClient,
        session: AsyncSession,
        test_listener_full: TestUser,
    ) -> None:
        """When play counts tie, order by username ascending."""
        a_id = _make_artist(session, username="beta")
        b_id = _make_artist(session, username="alpha")
        await session.commit()

        await _seed_popularity(session, a_id, plays=5)
        await _seed_popularity(session, b_id, plays=5)

        response = await async_client.get(
            f"{TEST_BASE_URL}/artist",
            params={"page": 1, "pageSize": 10},
            headers=auth_headers(test_listener_full.id, role="listener"),
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        ids = [item["id"] for item in data["artists"]]
        assert ids == [str(b_id), str(a_id)]

    async def test_pagination_pages_split_results(
        self,
        async_client: AsyncClient,
        session: AsyncSession,
        test_listener_full: TestUser,
    ) -> None:
        """Pagination should return two items on first page and the remainder on second page."""
        a_id = _make_artist(session, username="a")
        b_id = _make_artist(session, username="b")
        c_id = _make_artist(session, username="c")
        await session.commit()

        await _seed_popularity(session, a_id, plays=10)
        await _seed_popularity(session, b_id, plays=7)
        await _seed_popularity(session, c_id, plays=1)

        resp1 = await async_client.get(
            f"{TEST_BASE_URL}/artist",
            params={"page": 1, "pageSize": 2},
            headers=auth_headers(uuid.uuid4(), role="listener"),
        )
        assert resp1.status_code == status.HTTP_200_OK
        data1 = resp1.json()
        assert data1["total"] == 3
        assert data1["totalPages"] == 2
        assert [x["id"] for x in data1["artists"]] == [str(a_id), str(b_id)]

        resp2 = await async_client.get(
            f"{TEST_BASE_URL}/artist",
            params={"page": 2, "pageSize": 2},
            headers=auth_headers(uuid.uuid4(), role="listener"),
        )
        assert resp2.status_code == status.HTTP_200_OK
        data2 = resp2.json()
        assert [x["id"] for x in data2["artists"]] == [str(c_id)]

    async def test_non_artists_are_excluded(
        self,
        async_client: AsyncClient,
        session: AsyncSession,
    ) -> None:
        """Listeners must not appear in the artists list."""
        artist_id = _make_artist(session, username="artist")
        listener_id = uuid.uuid4()
        session.add(UserAccount(id=listener_id, role=UserRole.LISTENER, status=UserStatus.ACTIVE))
        session.add(UserProfile(id=listener_id, username="listener", full_name="Listener", birthdate=date(1995, 1, 1)))
        await session.commit()

        await _seed_popularity(session, artist_id, plays=1)

        response = await async_client.get(f"{TEST_BASE_URL}/artist")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        ids = [x["id"] for x in data["artists"]]
        assert ids == [str(artist_id)]

    async def test_invalid_query_params_return_422(
        self,
        async_client: AsyncClient,
    ) -> None:
        """Invalid page/pageSize should yield 422 Unprocessable Entity (FastAPI validation)."""
        r1 = await async_client.get(f"{TEST_BASE_URL}/artist", params={"page": 0, "pageSize": 10})
        r2 = await async_client.get(f"{TEST_BASE_URL}/artist", params={"page": 1, "pageSize": 0})
        r3 = await async_client.get(f"{TEST_BASE_URL}/artist", params={"page": 1, "pageSize": 101})
        assert r1.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert r2.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert r3.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
