import uuid

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_jwt_payload, require_admin
from app.main import app
from app.models.user import UserAccount

sync_engine = create_engine(settings.DATABASE_URL.replace("+asyncpg", ""))


def override_require_admin():
    return None


def override_get_jwt_payload():
    return {"role": "listener"}


def create_user_with_role(role: str) -> uuid.UUID:
    user_id = uuid.uuid4()
    with Session(sync_engine) as session:
        user = UserAccount(id=user_id, email="test@example.com", password="password", role=role)
        session.add(user)
        session.commit()
    return user_id


def test_01_patch_user_with_listener_role_to_artist():
    app.dependency_overrides[require_admin] = override_require_admin
    user_id = create_user_with_role("listener")
    client = TestClient(app)
    headers = {"Authorization": "Bearer admin_token"}
    response = client.patch(f"/users/admin/{user_id}/role", headers=headers)

    assert response.status_code == 200
    assert response.json() == {
        "id": str(user_id),
        "role": "artist",
    }
    with Session(sync_engine) as session:
        user = session.get(UserAccount, user_id)
        assert user.role == "artist"
    app.dependency_overrides = {}


def test_02_patch_user_with_artist_role_to_listener():
    app.dependency_overrides[require_admin] = override_require_admin
    user_id = create_user_with_role("artist")
    client = TestClient(app)
    headers = {"Authorization": "Bearer admin_token"}
    response = client.patch(f"/users/admin/{user_id}/role", headers=headers)

    assert response.status_code == 200
    assert response.json() == {
        "id": str(user_id),
        "role": "listener",
    }
    with Session(sync_engine) as session:
        user = session.get(UserAccount, user_id)
        assert user.role == "listener"
    app.dependency_overrides = {}


def test_03_patch_user_with_non_existent_id_returns_404():
    app.dependency_overrides[require_admin] = override_require_admin
    client = TestClient(app)
    user_id = uuid.uuid4()
    headers = {"Authorization": "Bearer admin_token"}
    response = client.patch(f"/users/admin/{user_id}/role", headers=headers)

    assert response.status_code == 404
    assert response.json() == {"type": "about:blank", "title": "Resource Not Found", "status": 404, "detail": f"Usuario con id: {user_id} no encontrado", "instance": f"/users/admin/{user_id}/role"}
    app.dependency_overrides = {}


def test_04_patch_user_role_without_admin_token_returns_401():
    user_id = uuid.uuid4()
    client = TestClient(app)
    response = client.patch(f"/users/admin/{user_id}/role")
    assert response.status_code == 401
    assert response.json() == {
        "type": "about:blank",
        "title": "Authentication Error",
        "status": 401,
        "detail": "Token de autenticación invalido o no proporcionado",
        "instance": f"/users/admin/{user_id}/role",
    }


def test_05_patch_user_role_with_non_admin_token_returns_401():
    app.dependency_overrides[get_jwt_payload] = override_get_jwt_payload
    user_id = uuid.uuid4()
    client = TestClient(app)
    headers = {"Authorization": f"Bearer {user_id}"}
    response = client.patch(f"/users/admin/{user_id}/role", headers=headers)
    assert response.status_code == 401
    assert response.json() == {"type": "about:blank", "title": "Authentication Error", "status": 401, "detail": "Se requiere privilegios de administrador", "instance": f"/users/admin/{user_id}/role"}
    app.dependency_overrides = {}


def test_06_patch_user_with_existent_account_and_non_exist_profile_returns_200():
    app.dependency_overrides[require_admin] = override_require_admin
    user_id = uuid.uuid4()
    user = UserAccount(id=user_id, email="test@example.com", password="password")
    with Session(sync_engine) as session:
        session.add(user)
        session.commit()
        user_id_str = str(user.id)
    client = TestClient(app)
    headers = {"Authorization": f"Bearer {user_id_str}"}
    response = client.patch(f"/users/admin/{user_id_str}/role", headers=headers)
    assert response.status_code == 200
    assert response.json() == {
        "id": user_id_str,
        "role": "artist",
    }
    app.dependency_overrides = {}


def test_07_when_patch_user_role_then_the_user_request_are_invalid():
    app.dependency_overrides[require_admin] = override_require_admin
    user_id = create_user_with_role("listener")
    client = TestClient(app)
    headers = {"Authorization": "Bearer admin_token"}
    response = client.patch(f"/users/admin/{user_id}/role", headers=headers)

    assert response.status_code == 200
    assert response.json() == {
        "id": str(user_id),
        "role": "artist",
    }
    app.dependency_overrides[get_jwt_payload] = lambda: {"user_id": str(user_id), "role": "listener"}
    response = client.get("/users/me", headers={"Authorization": f"Bearer {user_id}"})
    response.status_code == 401
    assert response.json() == {"type": "about:blank", "title": "Authentication Error", "status": 401, "detail": "El rol del usuario no coincide con el del token", "instance": "/users/me"}
    app.dependency_overrides = {}
