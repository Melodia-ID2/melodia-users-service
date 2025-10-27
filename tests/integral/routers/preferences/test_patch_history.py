import uuid
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from app.core.security import get_current_user_id, get_jwt_payload
from app.main import app
from app.core.config import settings
from sqlalchemy.orm import Session

from app.models.useraccount import UserAccount

sync_engine = create_engine(settings.DATABASE_URL.replace("+asyncpg", ""))

def test_01_patch_history_preferences_to_enabled_returns_200():
    user_id = uuid.uuid4()
    with Session(sync_engine) as session:
        user= UserAccount(id=user_id, preferences=0b0)
        session.add(user)
        session.commit()
    client = TestClient(app)
    headers = {"Authorization": "Bearer user_token"}
    app.dependency_overrides[get_current_user_id] = lambda: user_id
    response = client.patch("/preferences/history", headers=headers)
    assert response.status_code == 200
    assert response.json() == {"message": "Historial activado exitosamente."}
    with Session(sync_engine) as session:
        user = session.get(UserAccount, user_id)
        assert user.preferences & 0b1 == 0b1
    app.dependency_overrides = {}

def test_02_patch_history_preferences_to_disabled_returns_200():
    user_id = uuid.uuid4()
    with Session(sync_engine) as session:
        user= UserAccount(id=user_id, preferences=0b1)
        session.add(user)
        session.commit()
    client = TestClient(app)
    headers = {"Authorization": "Bearer user_token"}
    app.dependency_overrides[get_current_user_id] = lambda: user_id
    response = client.patch("/preferences/history", headers=headers)
    assert response.status_code == 200
    assert response.json() == {"message": "Historial desactivado exitosamente."}
    with Session(sync_engine) as session:
        user = session.get(UserAccount, user_id)
        assert user.preferences & 0b1 == 0b0
    app.dependency_overrides = {}

def test_03_patch_history_preferences_without_token_access_returns_401():
    client = TestClient(app)
    response = client.patch("/preferences/history")
    assert response.status_code == 401
    assert response.json() == {
        "type": "about:blank",
        "title": "Authentication Error",
        "status": 401,
        "detail": "Token de autenticación invalido o no proporcionado",
        "instance": "/preferences/history",
    }
def test_04_patch_history_preferences_with_non_existent_user_returns_401():
    user_id = uuid.uuid4()
    client = TestClient(app)
    headers = {"Authorization": "Bearer user_token"}
    app.dependency_overrides[get_jwt_payload] = lambda: {"user_id": str(user_id), "role": "listener"}
    response = client.patch("/preferences/history", headers=headers)
    assert response.status_code == 404
    assert response.json() == {
        "type": "about:blank",
        "title": "Resource Not Found",
        "status": 404,
        "detail": "Usuario no encontrado",
        "instance": "/preferences/history",
    }
    app.dependency_overrides = {}


