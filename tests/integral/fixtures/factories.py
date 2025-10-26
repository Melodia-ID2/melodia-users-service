import uuid
from dataclasses import dataclass
from datetime import datetime

import pytest

from app.models.regions import Country
from app.models.useraccount import UserAccount, UserRole, UserStatus
from app.models.usercredential import UserCredential
from app.models.userprofile import ArtistPhoto, SocialLink, UserGender, UserProfile


@dataclass
class TestUser:
    id: uuid.UUID
    account: UserAccount
    profile: UserProfile
    credentials: UserCredential


@dataclass
class TestArtist(TestUser):
    photos: list[ArtistPhoto]
    links: list[SocialLink]


@pytest.fixture
def test_listener_minimal_data():
    """Test data to create a minimal listener user."""
    id = uuid.uuid4()
    account = UserAccount(
        id=id,
        created_at=datetime.fromisoformat("2025-01-01T00:00:00"),
        last_login=datetime.fromisoformat("2025-01-01T00:00:00"),
        role=UserRole.LISTENER,
        status=UserStatus.ACTIVE,
        country=Country.AR,
        is_profile_completed=True,
    )
    profile = UserProfile(
        id=id,
        gender=UserGender.OTHER,
        following_count=0,
        followers_count=0,
    )
    credentials = UserCredential(
        user_id=id,
        email=f"test_{id.hex}@example.com",
        password="password",
    )
    return TestUser(id=id, account=account, profile=profile, credentials=credentials)


@pytest.fixture
def test_listener_full_data():
    """Test data to create a complete listener user."""
    id = uuid.uuid4()
    account = UserAccount(
        id=id,
        created_at=datetime.fromisoformat("2025-01-01T00:00:00"),
        last_login=datetime.fromisoformat("2025-01-01T00:00:00"),
        role=UserRole.LISTENER,
        status=UserStatus.ACTIVE,
        country=Country.AR,
        is_profile_completed=True,
    )
    profile = UserProfile(
        id=id,
        username=f"testuser_{id.hex[:8]}",
        full_name="Test User",
        birthdate=datetime.fromisoformat("2000-01-01").date(),
        gender=UserGender.OTHER,
        phone_number="1234567890",
        address="123 Main St",
        profile_photo="https://example.com/profile.jpg",
        bio="This is a test user",
        following_count=10,
        followers_count=10,
    )
    credentials = UserCredential(
        user_id=id,
        email=f"test_{id.hex}@example.com",
        password="password",
    )
    return TestUser(id=id, account=account, profile=profile, credentials=credentials)


@pytest.fixture
def test_artist_full_data():
    """Test data to create a complete artist."""
    id = uuid.uuid4()
    account = UserAccount(
        id=id,
        created_at=datetime.fromisoformat("2025-01-01T00:00:00"),
        last_login=datetime.fromisoformat("2025-01-01T00:00:00"),
        role=UserRole.ARTIST,
        status=UserStatus.ACTIVE,
        country=Country.AR,
        is_profile_completed=True,
    )
    profile = UserProfile(
        id=id,
        username=f"testuser_{id.hex[:8]}",
        full_name="Test User",
        birthdate=datetime.fromisoformat("2000-01-01").date(),
        gender=UserGender.OTHER,
        phone_number="1234567890",
        address="123 Main St",
        profile_photo="https://example.com/profile.jpg",
        bio="This is a test user",
        following_count=10,
        followers_count=10,
    )
    links = [
        SocialLink(id=uuid.uuid4(), artist_id=id, url=f"https://socialmedia.com/link_{i}")
        for i in range(1, 4)
    ]
    photos = [
        ArtistPhoto(
            id=uuid.uuid4(),
            artist_id=id,
            url=f"https://example.com/photo_{i}.jpg",
            position=i,
            uploaded_at=datetime.fromisoformat("2025-01-01T00:00:00"),
        )
        for i in range(1, 4)
    ]
    credentials = UserCredential(user_id=id, email=f"test_{id.hex}@example.com", password="password")
    return TestArtist(id=id, account=account, profile=profile, credentials=credentials, photos=photos, links=links)
