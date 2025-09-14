import pytest
from tests.integral.conftest import BASE_URL

from fastapi.testclient import TestClient
from app.main import app
from app.core.security import get_jwt_payload, require_admin
from app.models.user import UserAccount, UserProfile, RefreshToken
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
import uuid

from app.core.config import settings
sync_engine = create_engine(settings.DATABASE_URL.replace('+asyncpg', ''))

def override_require_admin():
    return None

def override_get_jwt_payload():
    return {"role": "listener"}

def test_01_delete_user_returns_204_and_deletes_user():
    app.dependency_overrides[require_admin] = override_require_admin
    user_id = uuid.uuid4()
    with Session(sync_engine) as session:
        user = UserAccount(id=user_id, email="test@example.com", password="password")
        user_profile = UserProfile(id=user_id)
        refresh_token = RefreshToken(user_id=user_id, token="sometoken")
        session.add(user)
        session.commit()
        session.add(user_profile)
        session.add(refresh_token)
        session.commit()
    client = TestClient(app)
    headers = {"Authorization": "Bearer admin_token"}
    response = client.delete(f"/users/{user_id}", headers=headers)
    assert response.status_code == 204
    with Session(sync_engine) as session:
        deleted_user = session.get(UserAccount, user_id)
        deleted_profile = session.get(UserProfile, user_id)
        deleted_token = session.execute(
            select(RefreshToken).where(RefreshToken.user_id == user_id)
        ).scalar_one_or_none()
        assert deleted_token is None
        assert deleted_profile is None
        assert deleted_user is None

def test_02_delete_user_with_many_tokens_deletes_all_tokens():
    app.dependency_overrides[require_admin] = override_require_admin
    user_id = uuid.uuid4()
    with Session(sync_engine) as session:
        user = UserAccount(id=user_id, email="test@example.com", password="password")
        user_profile = UserProfile(id=user_id)
        refresh_token1 = RefreshToken(user_id=user_id, token="token1")
        refresh_token2 = RefreshToken(user_id=user_id, token="token2")
        session.add(user)
        session.commit()
        session.add(user_profile)
        session.add(refresh_token1)
        session.add(refresh_token2)
        session.commit()
    client = TestClient(app)
    headers = {"Authorization": "Bearer admin_token"}
    response = client.delete(f"/users/{user_id}", headers=headers)
    assert response.status_code == 204
    with Session(sync_engine) as session:
        deleted_user = session.get(UserAccount, user_id)
        deleted_profile = session.get(UserProfile, user_id)
        deleted_token1 = session.execute(
            select(RefreshToken).where(RefreshToken.token == "token1")
        ).scalar_one_or_none()
        deleted_token2 = session.execute(
            select(RefreshToken).where(RefreshToken.token == "token2")
        ).scalar_one_or_none()
        assert deleted_token1 is None
        assert deleted_token2 is None
        assert deleted_profile is None
        assert deleted_user is None

def test_03_delete_nonexistent_user_returns_404():
    app.dependency_overrides[require_admin] = override_require_admin
    user_id = uuid.uuid4()
    client = TestClient(app)
    headers = {"Authorization": "Bearer admin_token"}
    response = client.delete(f"/users/{user_id}", headers=headers)
    assert response.status_code == 404
    assert response.json() == {
        "type": "about:blank",
        "title": "Resource Not Found",
        "status": 404,
        "detail": f"User with id: {user_id} not found",
        "instance": f"/users/{user_id}"
    }
    app.dependency_overrides = {}

def test_04_delete_user_without_admin_token_returns_401():
    user_id = uuid.uuid4()
    client = TestClient(app)
    response = client.delete(f"/users/{user_id}")
    assert response.status_code == 401
    assert response.json() == {
        "type": "about:blank",
        "title": "Authentication Error",
        "status": 401,
        "detail": "Invalid or missing authorization token",
        "instance": f"/users/{user_id}"
    }

def test_05_delete_user_with_non_admin_token_returns_401():
    app.dependency_overrides[get_jwt_payload] = override_get_jwt_payload
    user_id = uuid.uuid4()
    client = TestClient(app)
    headers = {"Authorization": f"Bearer {user_id}"}
    response = client.delete(f"/users/{user_id}", headers=headers)
    assert response.status_code == 401
    assert response.json() == {
        "type": "about:blank",
        "title": "Authentication Error",
        "status": 401,
        "detail": "Admin privileges required",
        "instance": f"/users/{user_id}"
    }
    app.dependency_overrides = {}