import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from tests.integral.fixtures.factories import TestArtist, TestUser


@pytest_asyncio.fixture
async def test_listener_full(session: AsyncSession, test_listener_full_data: TestUser):
    """Crea y persiste un usuario oyente completo."""
    session.add(test_listener_full_data.account)
    session.add(test_listener_full_data.credentials)
    session.add(test_listener_full_data.profile)
    await session.commit()
    await session.refresh(test_listener_full_data.account)
    return test_listener_full_data


@pytest_asyncio.fixture
async def test_listener_minimal(session: AsyncSession, test_listener_minimal_data: TestUser):
    """Crea y persiste un usuario oyente mínimo."""
    session.add(test_listener_minimal_data.account)
    session.add(test_listener_minimal_data.credentials)
    session.add(test_listener_minimal_data.profile)
    await session.commit()
    await session.refresh(test_listener_minimal_data.account)
    return test_listener_minimal_data


@pytest_asyncio.fixture
async def test_artist_full(session: AsyncSession, test_artist_full_data: TestArtist):
    """Crea y persiste un artista completo, con fotos y links."""
    session.add(test_artist_full_data.account)
    session.add(test_artist_full_data.credentials)
    session.add(test_artist_full_data.profile)
    
    for photo in test_artist_full_data.photos:
        session.add(photo)
    
    for link in test_artist_full_data.links:
        session.add(link)
    
    await session.commit()
    await session.refresh(test_artist_full_data.account)
    return test_artist_full_data
