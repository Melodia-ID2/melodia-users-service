import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import get_jwt_payload, require_admin
from app.models.user import UserAccount, UserProfile
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
import uuid

from app.core.config import settings
sync_engine = create_engine(settings.DATABASE_URL.replace('+asyncpg', ''))

def override_require_admin():
    return None

def override_get_jwt_payload():
    return {"role": "listener"}

def create_user_with_role(role: str) -> uuid.UUID:
    user_id = uuid.uuid4()
    with Session(sync_engine) as session:
        user = UserAccount(id=user_id, email="test@example.com", password="password")
        user_profile = UserProfile(id=user_id, role=role)
        session.add(user)
        session.add(user_profile)

        session.commit()
    return user_id

def test_01_patch_user_with_listener_role_to_artist():
    app.dependency_overrides[require_admin] = override_require_admin
    user_id = create_user_with_role("listener")
    client = TestClient(app)
    headers = {"Authorization": "Bearer admin_token"}
    response = client.patch(f"/users/{user_id}/role", headers=headers)

    assert response.status_code == 200
    assert response.json()=={
        "user": {
            "id": str(user_id),
            "email": "test@example.com",
            "username": None,
            "role": "artist",
            "status": "active"
        }
    }
    with Session(sync_engine) as session:
        user_profile = session.get(UserProfile, user_id)
        assert user_profile.role == "artist"
    app.dependency_overrides = {}

def test_02_patch_user_with_artist_role_to_listener():
    app.dependency_overrides[require_admin] = override_require_admin
    user_id = create_user_with_role("artist")
    client = TestClient(app)
    headers = {"Authorization": "Bearer admin_token"}
    response = client.patch(f"/users/{user_id}/role", headers=headers)

    assert response.status_code == 200
    assert response.json()=={
        "user": {
            "id": str(user_id),
            "email": "test@example.com",
            "username": None,
            "role": "listener",
            "status": "active"
        }
    }
    with Session(sync_engine) as session:
        user_profile = session.get(UserProfile, user_id)
        assert user_profile.role == "listener"
    app.dependency_overrides = {}

def test_03_patch_user_with_non_existent_id_returns_404():
    app.dependency_overrides[require_admin] = override_require_admin
    client = TestClient(app)
    user_id = uuid.uuid4()
    headers = {"Authorization": "Bearer admin_token"}
    response = client.patch(f"/users/{user_id}/role", headers=headers)

    assert response.status_code == 404
    assert response.json() == {
        "type": "about:blank",
        "title": "Resource Not Found",
        "status": 404,
        "detail": f"User with id: {user_id} not found",
        "instance": f"/users/{user_id}/role"
    }
    app.dependency_overrides = {}

def test_04_patch_user_role_without_admin_token_returns_401():
    user_id = uuid.uuid4()
    client = TestClient(app)
    response = client.patch(f"/users/{user_id}/role")
    assert response.status_code == 401
    assert response.json() == {
        "type": "about:blank",
        "title": "Authentication Error",
        "status": 401,
        "detail": "Invalid or missing authorization token",
        "instance": f"/users/{user_id}/role"
    }

def test_05_patch_user_role_with_non_admin_token_returns_401():
    app.dependency_overrides[get_jwt_payload] = override_get_jwt_payload
    user_id = uuid.uuid4()
    client = TestClient(app)
    headers = {"Authorization": f"Bearer {user_id}"}
    response = client.patch(f"/users/{user_id}/role", headers=headers)
    assert response.status_code == 401
    assert response.json() == {
        "type": "about:blank",
        "title": "Authentication Error",
        "status": 401,
        "detail": "Admin privileges required",
        "instance": f"/users/{user_id}/role"
    }
    app.dependency_overrides = {}