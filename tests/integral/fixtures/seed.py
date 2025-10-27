import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from tests.integral.fixtures.factories import TestArtist, TestUser


@pytest_asyncio.fixture
async def test_listener_full(session: AsyncSession, test_listener_full_data: TestUser):
    """Create and persist a complete listener user."""
    session.add(test_listener_full_data.account)
    session.add(test_listener_full_data.credentials)
    session.add(test_listener_full_data.profile)
    await session.commit()
    await session.refresh(test_listener_full_data.account)
    return test_listener_full_data


@pytest_asyncio.fixture
async def test_listener_minimal(session: AsyncSession, test_listener_minimal_data: TestUser):
    """Create and persist a minimal listener user."""
    session.add(test_listener_minimal_data.account)
    session.add(test_listener_minimal_data.credentials)
    session.add(test_listener_minimal_data.profile)
    await session.commit()
    await session.refresh(test_listener_minimal_data.account)
    return test_listener_minimal_data


@pytest_asyncio.fixture
async def test_artist_full(session: AsyncSession, test_artist_full_data: TestArtist):
    """Create and persist a complete artist with photos and links."""
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
