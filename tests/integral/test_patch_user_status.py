from fastapi.testclient import TestClient
from app.main import app
from app.core.security import get_jwt_payload, require_admin
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
import uuid

from app.core.config import settings
from app.models.user import UserAccount, UserProfile
sync_engine = create_engine(settings.DATABASE_URL.replace('+asyncpg', ''))

def override_require_admin():
    return None

def create_user_with_status(status: str) -> uuid.UUID:
    user_id = uuid.uuid4()
    with Session(sync_engine) as session:
        user = UserAccount(id=user_id, email="test@example.com", password="password", status=status)
        user_profile = UserProfile(id=user_id)
        session.add(user)
        session.add(user_profile)

        session.commit()
    return user_id

def override_get_jwt_payload():
    return {"role": "listener"}

def test_01_patch_user_status_from_active_to_blocked():
    app.dependency_overrides[require_admin] = override_require_admin
    user_id = create_user_with_status("active")
    client = TestClient(app)
    headers = {"Authorization": f"Bearer {user_id}"}
    response = client.patch(f"/users/{user_id}/status", headers=headers)
    assert response.status_code == 200
    assert response.json() == {
        "id": str(user_id),
        "email": "test@example.com",
        "username": None,
        "role": "listener",
        "status": "blocked",
        "fullName": None,
        "phoneNumber": None,
        "address": None,
        "lastLogin": None,
        "createdAt": response.json()["createdAt"],
        "birthdate": None,
        "profilePhoto": None
    }
    with Session(sync_engine) as session:
        user_account = session.get(UserAccount, user_id)
        assert user_account.status == "blocked"
    app.dependency_overrides = {}

def test_02_patch_user_status_from_blocked_to_active():
    app.dependency_overrides[require_admin] = override_require_admin
    user_id = create_user_with_status("blocked")
    client = TestClient(app)
    headers = {"Authorization": f"Bearer {user_id}"}
    response = client.patch(f"/users/{user_id}/status", headers=headers)
    assert response.status_code == 200
    assert response.json() == {
        "id": str(user_id),
        "email": "test@example.com",
        "username": None,
        "role": "listener",
        "status": "active",
        "fullName": None,
        "phoneNumber": None,
        "address": None,
        "lastLogin": None,
        "createdAt": response.json()["createdAt"],
        "birthdate": None,
        "profilePhoto": None
    }
    with Session(sync_engine) as session:
        user_account = session.get(UserAccount, user_id)
        assert user_account.status == "active"
    app.dependency_overrides = {}

def test_03_patch_user_status_with_non_existent_id_returns_404():
    app.dependency_overrides[require_admin] = override_require_admin
    user_id = uuid.uuid4()
    client = TestClient(app)
    headers = {"Authorization": f"Bearer {user_id}"}
    response = client.patch(f"/users/{user_id}/status", headers=headers)
    assert response.status_code == 404
    assert response.json() == {
        "type": "about:blank",
        "title": "Resource Not Found",
        "status": 404,
        "detail": f"User with id: {user_id} not found",
        "instance": f"/users/{user_id}/status"
    }
    app.dependency_overrides = {}

def test_04_patch_user_status_without_admin_token_returns_401():
    user_id = uuid.uuid4()
    client = TestClient(app)
    response = client.patch(f"/users/{user_id}/status")
    assert response.status_code == 401
    assert response.json() == {
        "type": "about:blank",
        "title": "Authentication Error",
        "status": 401,
        "detail": "Invalid or missing authorization token",
        "instance": f"/users/{user_id}/status"
    }

def test_05_patch_user_status_with_non_admin_token_returns_401():
    app.dependency_overrides[get_jwt_payload] = override_get_jwt_payload
    user_id = uuid.uuid4()
    client = TestClient(app)
    headers = {"Authorization": f"Bearer {user_id}"}
    response = client.patch(f"/users/{user_id}/status", headers=headers)
    assert response.status_code == 401
    assert response.json() == {
        "type": "about:blank",
        "title": "Authentication Error",
        "status": 401,
        "detail": "Admin privileges required",
        "instance": f"/users/{user_id}/status"
    }
    app.dependency_overrides = {}

def test_06_patch_user_status_with_existent_account_and_non_exist_profile_returns_200():
    app.dependency_overrides[require_admin] = override_require_admin
    user_id = uuid.uuid4()
    user = UserAccount(id=user_id, email="test@example.com", password="password")
    with Session(sync_engine) as session:
        session.add(user)
        session.commit()
        user_id_str = str(user.id)
        user_email = user.email
    client = TestClient(app)
    headers = {"Authorization": f"Bearer {user_id_str}"}
    response = client.patch(f"/users/{user_id_str}/status", headers=headers)
    assert response.status_code == 200
    assert response.json() == {
        "id": user_id_str, 
        "email": user_email, 
        "username": None, 
        "role": "listener", 
        "status": "blocked",
        "fullName": None, 
        "phoneNumber": None, 
        "address": None,
        "lastLogin": None,
        "createdAt": response.json()["createdAt"],
        "birthdate": None,
        "profilePhoto": None
    }
    app.dependency_overrides = {}