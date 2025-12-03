import uuid
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from app.core.security import get_current_user_id, get_jwt_payload
from app.main import app
from app.core.config import settings
from sqlalchemy.orm import Session
from app.constants.notification_flags import BIT_AUTOPLAY

from app.models.useraccount import UserAccount

sync_engine = create_engine(settings.DATABASE_URL.replace("+asyncpg", ""))

def test_01_patch_autoplay_preferences_to_enabled_returns_200():
    user_id = uuid.uuid4()
    with Session(sync_engine) as session:
        user= UserAccount(id=user_id, preferences=0)
        session.add(user)
        session.commit()
    
    client = TestClient(app)
    headers = {"Authorization": "Bearer user_token"}
    app.dependency_overrides[get_current_user_id] = lambda: user_id
    
    response = client.patch("/preferences/autoplay", headers=headers)
    
    assert response.status_code == 200
    assert response.status_code == 200
    assert response.json() == {"autoplay": True}
    
    with Session(sync_engine) as session:
        user = session.get(UserAccount, user_id)
        assert user is not None
        assert user.preferences & BIT_AUTOPLAY == BIT_AUTOPLAY
    
    app.dependency_overrides = {}

def test_02_patch_autoplay_preferences_to_disabled_returns_200():
    user_id = uuid.uuid4()
    with Session(sync_engine) as session:
        user= UserAccount(id=user_id, preferences=BIT_AUTOPLAY)
        session.add(user)
        session.commit()
    
    client = TestClient(app)
    headers = {"Authorization": "Bearer user_token"}
    app.dependency_overrides[get_current_user_id] = lambda: user_id
    
    response = client.patch("/preferences/autoplay", headers=headers)
    
    assert response.status_code == 200
    assert response.status_code == 200
    assert response.json() == {"autoplay": False}
    
    with Session(sync_engine) as session:
        user = session.get(UserAccount, user_id)
        assert user is not None
        assert user.preferences & BIT_AUTOPLAY == 0
    
    app.dependency_overrides = {}

def test_03_get_autoplay_preferences_returns_correct_status():
    user_id = uuid.uuid4()
    with Session(sync_engine) as session:
        user= UserAccount(id=user_id, preferences=BIT_AUTOPLAY)
        session.add(user)
        session.commit()
    
    client = TestClient(app)
    headers = {"Authorization": "Bearer user_token"}
    app.dependency_overrides[get_current_user_id] = lambda: user_id
    
    response = client.get("/preferences/autoplay", headers=headers)
    
    assert response.status_code == 200
    assert response.status_code == 200
    assert response.json() == {"autoplay": True}
    
    app.dependency_overrides = {}
