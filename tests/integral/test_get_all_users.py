import uuid

import pytest
from httpx import AsyncClient, Response
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

# Engine síncrono para manipulación directa en tests
from app.core.config import settings
from app.core.security import get_jwt_payload, require_admin
from app.main import app
from app.models.useraccount import UserAccount
from app.models.usercredential import UserCredential
from app.models.userprofile import UserProfile

sync_engine = create_engine(settings.DATABASE_URL.replace("+asyncpg", ""))


def insert_n_users(n: int) -> list[uuid.UUID]:
    user_ids: list[uuid.UUID] = []
    with Session(sync_engine) as session:
        for i in range(1, n + 1):
            user_id = uuid.uuid4()
            user_ids.append(user_id)
            user = UserAccount(id=user_id)
            user_credentials = UserCredential(user_id=user_id, email=f"email{i}@example.com", password="password")
            user_profile = UserProfile(id=user_id)
            session.add(user)
            session.add(user_credentials)
            session.add(user_profile)
        session.commit()
    return user_ids


def assert_n_users_in_response(response: Response, n: int, user_ids: list[uuid.UUID]):
    assert response.status_code == 200
    data = response.json()
    assert "users" in data
    assert len(data["users"]) == n
    for i in range(n):
        user = data["users"][i]
        assert user["id"] == str(user_ids[i])
        assert user["email"] == f"email{i + 1}@example.com"
        assert user["username"] is None
        assert user["role"] == "listener"
        assert user["status"] == "active"


def override_require_admin():
    return None


def override_get_jwt_payload():
    return {"role": "listener"}


@pytest.mark.asyncio
async def test_01_get_all_without_admin_token_returns_401(async_client: AsyncClient):
    r = await async_client.get("/admin")
    assert r.status_code == 401
    assert r.json() == {"type": "about:blank", "title": "Authentication Error", "status": 401, "detail": "Token de autenticación invalido o no proporcionado", "instance": "/admin"}


@pytest.mark.asyncio
async def test_02_get_all_with_admin_token_and_no_users_returns_empty_list(async_client: AsyncClient):
    app.dependency_overrides[require_admin] = override_require_admin
    response = await async_client.get("/admin", headers={"Authorization": "Bearer admin_token"})
    assert response.status_code == 200
    assert response.json()["users"] == []
    app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_03_get_all_with_admin_token_and_one(async_client: AsyncClient):
    user_ids = insert_n_users(1)
    app.dependency_overrides[require_admin] = override_require_admin
    response = await async_client.get("/admin", headers={"Authorization": "Bearer admin_token"})
    assert_n_users_in_response(response, 1, user_ids)
    app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_04_get_all_with_admin_token_and_multiple(async_client: AsyncClient):
    n = 5
    user_ids = insert_n_users(n)
    app.dependency_overrides[require_admin] = override_require_admin
    response = await async_client.get("/admin", headers={"Authorization": "Bearer admin_token"})
    assert_n_users_in_response(response, n, user_ids)
    app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_05_get_all_without_admin_role_returns_401(async_client: AsyncClient):
    app.dependency_overrides[get_jwt_payload] = override_get_jwt_payload
    response = await async_client.get("/admin", headers={"Authorization": "Bearer admin_token"})
    assert response.status_code == 401
    assert response.json() == {"type": "about:blank", "title": "Authentication Error", "status": 401, "detail": "Se requiere privilegios de administrador", "instance": "/admin"}
    app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_06_get_all_with_existent_account_and_non_exist_profile_returns_200(async_client: AsyncClient):
    app.dependency_overrides[require_admin] = override_require_admin
    user_id = uuid.uuid4()
    user = UserAccount(id=user_id)
    user_credentials = UserCredential(user_id=user_id, email="test@example.com", password="password")
    with Session(sync_engine) as session:
        session.add(user)
        session.add(user_credentials)
        session.commit()
        user_id_str = str(user.id)
    response = await async_client.get("/admin", headers={"Authorization": "Bearer admin_token"})

    assert response.status_code == 200
    assert response.json()["users"] == [{"id": user_id_str, "email": "test@example.com", "username": None, "role": "listener", "status": "active"}]
    app.dependency_overrides = {}
