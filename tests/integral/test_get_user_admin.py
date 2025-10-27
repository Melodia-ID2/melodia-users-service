import uuid
from datetime import date, datetime

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import require_admin
from app.main import app
from app.models.useraccount import UserAccount
from app.models.usercredential import UserCredential
from app.models.userprofile import UserProfile

sync_engine = create_engine(settings.DATABASE_URL.replace("+asyncpg", ""))


def test_01_get_user_admin_returns_200_and_user_data():
    app.dependency_overrides[require_admin] = lambda: None
    user_id = uuid.uuid4()
    custom_created_at = datetime(2025, 1, 1, 12, 0, 0)
    custom_last_login = datetime(2025, 6, 1, 12, 0, 0)
    custom_birthdate = date(2000, 1, 1)
    custom_username = "admin_test_user"
    custom_full_name = "Admin Test User"
    with Session(sync_engine) as session:
        user = UserAccount(id=user_id, last_login=custom_last_login, created_at=custom_created_at)
        user_credential = UserCredential(user_id=user_id, email="test@example.com", password="password")
        user_profile = UserProfile(id=user_id, username=custom_username, full_name=custom_full_name, birthdate=custom_birthdate)
        session.add(user)
        session.add(user_credential)
        session.add(user_profile)
        session.commit()
    client = TestClient(app)
    headers = {"Authorization": "Bearer admin_token"}
    response = client.get(f"/admin/{user_id}", headers=headers)
    assert response.status_code == 200
    assert response.json() == {
        "id": str(user_id),
        "email": "test@example.com",
        "username": custom_username,
        "role": "listener",
        "status": "active",
        "fullName": custom_full_name,
        "country": "AR",
        "birthdate": "2000-01-01",
        "phoneNumber": None,
        "address": None,
        "profilePhoto": None,
        "lastLogin": "2025-06-01T12:00:00",
        "createdAt": "2025-01-01T12:00:00",
    }
    app.dependency_overrides = {}
