from datetime import date, datetime
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import require_admin
from app.models.user import UserAccount, UserProfile
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
import uuid

from app.core.config import settings
sync_engine = create_engine(settings.DATABASE_URL.replace('+asyncpg', ''))


def test_01_get_user_admin_returns_200_and_user_data():
    app.dependency_overrides[require_admin] = lambda: None
    user_id = uuid.uuid4()
    custom_created_at = datetime(2025, 1, 1, 12, 0, 0)
    custom_last_login = datetime(2025, 6, 1, 12, 0, 0)
    custom_birthdate = date(2000, 1, 1)
    with Session(sync_engine) as session:
        user = UserAccount(id=user_id, email="test@example.com", password="password", last_login=custom_last_login, created_at=custom_created_at)
        user_profile = UserProfile(id=user_id, birthdate=custom_birthdate)
        session.add(user)
        session.add(user_profile)
        session.commit()
    client = TestClient(app)
    headers = {"Authorization": "Bearer admin_token"}
    response = client.get(f"/users/admin/{user_id}", headers=headers)
    assert response.status_code == 200
    assert response.json() == {
        "id": str(user_id),
        "email": "test@example.com",
        "username": None,
        "role": "listener",
        "status": "active",
        "fullName": None,
        "birthdate": "2000-01-01",
        "phoneNumber": None,
        "address": None,
        "profilePhoto": None,
        "lastLogin": "2025-06-01T12:00:00",
        "createdAt": "2025-01-01T12:00:00",
    }
    app.dependency_overrides = {}
