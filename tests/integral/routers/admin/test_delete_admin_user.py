import uuid

import pytest
from httpx import AsyncClient
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.useraccount import UserAccount
from app.models.usercredential import UserCredential
from app.models.userprofile import UserProfile, ArtistPhoto, SocialLink
from tests.integral.conftest import TEST_BASE_URL, TestArtist, TestUser, auth_headers


@pytest.mark.asyncio
class TestAdminDeleteUser:
    """Tests for the DELETE /admin/{user_id} endpoint."""

    async def test_delete_user_without_admin_token_returns_401(self, async_client: AsyncClient, test_listener_minimal: TestUser) -> None:
        """Attempting to delete a user without authentication should fail."""
        response = await async_client.delete(f"{TEST_BASE_URL}/admin/{test_listener_minimal.id}")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json() == {
            "type": "about:blank",
            "title": "Authentication Error",
            "status": status.HTTP_401_UNAUTHORIZED,
            "detail": "Token de autenticación invalido o no proporcionado",
            "instance": f"/admin/{test_listener_minimal.id}",
        }

    async def test_delete_user_with_non_admin_role_returns_401(self, async_client: AsyncClient, test_listener_minimal: TestUser, test_listener_full: TestUser) -> None:
        """Attempting to delete a user with non-admin role should fail."""
        response = await async_client.delete(
            f"{TEST_BASE_URL}/admin/{test_listener_full.id}",
            headers=auth_headers(test_listener_minimal.id, role="listener")
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json() == {
            "type": "about:blank",
            "title": "Authentication Error",
            "status": status.HTTP_401_UNAUTHORIZED,
            "detail": "Se requiere privilegios de administrador",
            "instance": f"/admin/{test_listener_full.id}",
        }

    async def test_delete_listener_minimal_success(self, async_client: AsyncClient, test_listener_minimal: TestUser, session: AsyncSession) -> None:
        """Successfully delete a minimal listener user."""
        user_id = test_listener_minimal.id
        
        response = await async_client.delete(
            f"{TEST_BASE_URL}/admin/{user_id}",
            headers=auth_headers(uuid.uuid4(), role="admin")
        )
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert response.text == ""
        
        await session.commit()
        session.expire_all()
        account = await session.get(UserAccount, user_id)
        assert account is None
        
        result = await session.execute(select(UserCredential).where(UserCredential.user_id == user_id))
        credentials = result.scalars().first()
        assert credentials is None
        
        profile = await session.get(UserProfile, user_id)
        assert profile is None

    async def test_delete_listener_full_success(self, async_client: AsyncClient, test_listener_full: TestUser, session: AsyncSession, monkeypatch: pytest.MonkeyPatch) -> None:
        """Successfully delete a complete listener user with profile photo."""
        from unittest.mock import Mock
        
        mock_destroy = Mock()
        monkeypatch.setattr("app.services.users_service.cloudinary.uploader.destroy", mock_destroy)
        
        user_id = test_listener_full.id
        
        response = await async_client.delete(
            f"{TEST_BASE_URL}/admin/{user_id}",
            headers=auth_headers(uuid.uuid4(), role="admin")
        )
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert response.text == ""
        
        mock_destroy.assert_called_once_with(public_id=f"user-photo-profile/{user_id}")
        
        await session.commit()
        session.expire_all()
        account = await session.get(UserAccount, user_id)
        assert account is None
        
        result = await session.execute(select(UserCredential).where(UserCredential.user_id == user_id))
        credentials = result.scalars().first()
        assert credentials is None
        
        profile = await session.get(UserProfile, user_id)
        assert profile is None

    async def test_delete_artist_with_photos_and_links_success(self, async_client: AsyncClient, test_artist_full: TestArtist, session: AsyncSession, monkeypatch: pytest.MonkeyPatch) -> None:
        """Successfully delete an artist user with photos and social links."""
        from unittest.mock import Mock
        
        mock_destroy = Mock()
        monkeypatch.setattr("app.services.users_service.cloudinary.uploader.destroy", mock_destroy)
        
        user_id = test_artist_full.id
        photo_ids = [photo.id for photo in test_artist_full.photos]
        link_ids = [link.id for link in test_artist_full.links]
        
        response = await async_client.delete(
            f"{TEST_BASE_URL}/admin/{user_id}",
            headers=auth_headers(uuid.uuid4(), role="admin")
        )
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert response.text == ""
        
        mock_destroy.assert_called_once_with(public_id=f"user-photo-profile/{user_id}")
        
        await session.commit()
        session.expire_all()
        account = await session.get(UserAccount, user_id)
        assert account is None
        
        result = await session.execute(select(UserCredential).where(UserCredential.user_id == user_id))
        credentials = result.scalars().first()
        assert credentials is None
        
        profile = await session.get(UserProfile, user_id)
        assert profile is None
        
        for photo_id in photo_ids:
            photo = await session.get(ArtistPhoto, photo_id)
            assert photo is None
        
        for link_id in link_ids:
            link = await session.get(SocialLink, link_id)
            assert link is None

    async def test_delete_nonexistent_user_returns_404(self, async_client: AsyncClient) -> None:
        """Attempting to delete a non-existent user should return 404."""
        nonexistent_id = uuid.uuid4()
        
        response = await async_client.delete(
            f"{TEST_BASE_URL}/admin/{nonexistent_id}",
            headers=auth_headers(uuid.uuid4(), role="admin")
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json() == {
            "type": "about:blank",
            "title": "Resource Not Found",
            "status": status.HTTP_404_NOT_FOUND,
            "detail": f"Usuario con id: {nonexistent_id} no encontrado",
            "instance": f"/admin/{nonexistent_id}",
        }

    async def test_delete_user_without_profile_photo_success(self, async_client: AsyncClient, test_listener_minimal: TestUser, session: AsyncSession, monkeypatch: pytest.MonkeyPatch) -> None:
        """Successfully delete a user without profile photo (Cloudinary not called)."""
        from unittest.mock import Mock
        
        mock_destroy = Mock()
        monkeypatch.setattr("app.services.users_service.cloudinary.uploader.destroy", mock_destroy)
        
        user_id = test_listener_minimal.id
        
        response = await async_client.delete(
            f"{TEST_BASE_URL}/admin/{user_id}",
            headers=auth_headers(uuid.uuid4(), role="admin")
        )
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        mock_destroy.assert_not_called()
        
        await session.commit()
        session.expire_all()
        account = await session.get(UserAccount, user_id)
        assert account is None

    async def test_delete_user_idempotent_returns_404_on_second_delete(self, async_client: AsyncClient, test_listener_minimal: TestUser) -> None:
        """Deleting the same user twice should return 404 on the second attempt."""
        user_id = test_listener_minimal.id
        admin_headers = auth_headers(uuid.uuid4(), role="admin")
        
        response1 = await async_client.delete(
            f"{TEST_BASE_URL}/admin/{user_id}",
            headers=admin_headers
        )
        assert response1.status_code == status.HTTP_204_NO_CONTENT
        
        response2 = await async_client.delete(
            f"{TEST_BASE_URL}/admin/{user_id}",
            headers=admin_headers
        )
        assert response2.status_code == status.HTTP_404_NOT_FOUND
        assert response2.json()["detail"] == f"Usuario con id: {user_id} no encontrado"
