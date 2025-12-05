import uuid
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.security import get_current_user_id
from app.main import app
from app.core.config import settings
from app.models.useraccount import UserAccount
from app.models.user_preferred_genre import UserPreferredGenre

sync_engine = create_engine(settings.DATABASE_URL.replace("+asyncpg", ""))


def test_01_put_preferred_genres_saves_genres():
    """Test that PUT /preferences/genres saves the genres correctly."""
    user_id = uuid.uuid4()
    with Session(sync_engine) as session:
        user = UserAccount(id=user_id)
        session.add(user)
        session.commit()
    
    client = TestClient(app)
    headers = {"Authorization": "Bearer user_token"}
    app.dependency_overrides[get_current_user_id] = lambda: user_id
    
    response = client.put(
        "/preferences/genres",
        headers=headers,
        json={"genres": ["POP", "ROCK", "JAZZ"]}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert sorted(data["genres"]) == ["JAZZ", "POP", "ROCK"]
    
    # Verify in database
    with Session(sync_engine) as session:
        genres = session.query(UserPreferredGenre).filter(
            UserPreferredGenre.user_id == user_id
        ).all()
        assert len(genres) == 3
        genre_codes = sorted([g.genre_code for g in genres])
        assert genre_codes == ["JAZZ", "POP", "ROCK"]
    
    app.dependency_overrides = {}


def test_02_get_preferred_genres_returns_saved_genres():
    """Test that GET /preferences/genres returns the saved genres."""
    user_id = uuid.uuid4()
    with Session(sync_engine) as session:
        user = UserAccount(id=user_id)
        session.add(user)
        session.commit()

    with Session(sync_engine) as session:
        session.add(UserPreferredGenre(user_id=user_id, genre_code="INDIE"))
        session.add(UserPreferredGenre(user_id=user_id, genre_code="METAL"))
        session.commit()
    
    client = TestClient(app)
    headers = {"Authorization": "Bearer user_token"}
    app.dependency_overrides[get_current_user_id] = lambda: user_id
    
    response = client.get("/preferences/genres", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert sorted(data["genres"]) == ["INDIE", "METAL"]
    
    app.dependency_overrides = {}


def test_03_put_preferred_genres_replaces_existing():
    """Test that PUT /preferences/genres replaces existing genres."""
    user_id = uuid.uuid4()
    # Crear usuario y confirmar la transacción antes de insertar los géneros existentes.
    with Session(sync_engine) as session:
        user = UserAccount(id=user_id)
        session.add(user)
        session.commit()

    with Session(sync_engine) as session:
        session.add(UserPreferredGenre(user_id=user_id, genre_code="OLD1"))
        session.add(UserPreferredGenre(user_id=user_id, genre_code="OLD2"))
        session.commit()
    
    client = TestClient(app)
    headers = {"Authorization": "Bearer user_token"}
    app.dependency_overrides[get_current_user_id] = lambda: user_id
    
    response = client.put(
        "/preferences/genres",
        headers=headers,
        json={"genres": ["NEW1"]}
    )
    
    assert response.status_code == 200
    
    # Verify old genres are deleted
    with Session(sync_engine) as session:
        genres = session.query(UserPreferredGenre).filter(
            UserPreferredGenre.user_id == user_id
        ).all()
        assert len(genres) == 1
        assert genres[0].genre_code == "NEW1"
    
    app.dependency_overrides = {}


def test_04_get_preferred_genres_returns_empty_for_new_user():
    """Test that GET /preferences/genres returns empty list for user with no genres."""
    user_id = uuid.uuid4()
    with Session(sync_engine) as session:
        user = UserAccount(id=user_id)
        session.add(user)
        session.commit()
    
    client = TestClient(app)
    headers = {"Authorization": "Bearer user_token"}
    app.dependency_overrides[get_current_user_id] = lambda: user_id
    
    response = client.get("/preferences/genres", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["genres"] == []
    
    app.dependency_overrides = {}


def test_05_put_preferred_genres_validates_max_5():
    """Test that PUT /preferences/genres rejects more than 5 genres."""
    user_id = uuid.uuid4()
    with Session(sync_engine) as session:
        user = UserAccount(id=user_id)
        session.add(user)
        session.commit()
    
    client = TestClient(app)
    headers = {"Authorization": "Bearer user_token"}
    app.dependency_overrides[get_current_user_id] = lambda: user_id
    
    response = client.put(
        "/preferences/genres",
        headers=headers,
        json={"genres": ["G1", "G2", "G3", "G4", "G5", "G6"]}  # 6 genres
    )
    
    assert response.status_code == 422  # Validation error
    
    app.dependency_overrides = {}


def test_06_put_preferred_genres_normalizes_to_uppercase():
    """Test that PUT /preferences/genres normalizes genres to uppercase."""
    user_id = uuid.uuid4()
    with Session(sync_engine) as session:
        user = UserAccount(id=user_id)
        session.add(user)
        session.commit()
    
    client = TestClient(app)
    headers = {"Authorization": "Bearer user_token"}
    app.dependency_overrides[get_current_user_id] = lambda: user_id
    
    response = client.put(
        "/preferences/genres",
        headers=headers,
        json={"genres": ["pop", "Rock", "JAZZ"]}  # Mixed case
    )
    
    assert response.status_code == 200
    
    # Verify all are uppercase in database
    with Session(sync_engine) as session:
        genres = session.query(UserPreferredGenre).filter(
            UserPreferredGenre.user_id == user_id
        ).all()
        genre_codes = sorted([g.genre_code for g in genres])
        assert genre_codes == ["JAZZ", "POP", "ROCK"]
    
    app.dependency_overrides = {}
