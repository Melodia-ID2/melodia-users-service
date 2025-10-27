from unittest.mock import Mock

import pytest
from httpx import AsyncClient
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.userprofile import UserProfile
from tests.integral.conftest import TEST_BASE_URL, TestUser, auth_headers


@pytest.mark.asyncio
class TestPatchProfilePhoto:
    """Tests for PATCH /me/profile-photo endpoint."""

    async def test_update_profile_photo_success(self, async_client: AsyncClient, test_listener_full: TestUser, monkeypatch: pytest.MonkeyPatch, session: AsyncSession) -> None:
        """Successfully update profile photo with mocked Cloudinary."""
        new_url = f"https://res.cloudinary.com/test/image/upload/v123/user-photo-profile/{test_listener_full.id}.jpg"
        mock_upload = Mock(return_value={"secure_url": new_url})
        monkeypatch.setattr("app.services.users_service.cloudinary.uploader.upload", mock_upload)

        fake_image = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
        files = {"file": ("profile.jpg", fake_image, "image/jpeg")}

        response = await async_client.patch(
            f"{TEST_BASE_URL}/me/profile-photo",
            headers=auth_headers(test_listener_full.id, role="listener"),
            files=files,
        )

        assert response.status_code == status.HTTP_200_OK, \
            f"Expected status code 200, got {response.status_code}. Response: {response.text}"
        assert response.json() == {"profile_photo": new_url}

        mock_upload.assert_called_once()
        call_args = mock_upload.call_args
        assert call_args[0][0] == fake_image
        assert call_args[1]["folder"] == "user-photo-profile"
        assert call_args[1]["public_id"] == str(test_listener_full.id)
        assert call_args[1]["overwrite"] is True

        await session.commit()
        session.expire_all()
        profile = await session.get(UserProfile, test_listener_full.id)
        assert profile is not None
        assert profile.profile_photo == new_url

    async def test_update_profile_photo_cloudinary_failure(self, async_client: AsyncClient, test_listener_full: TestUser, monkeypatch: pytest.MonkeyPatch) -> None:
        """Handle Cloudinary upload failure gracefully."""
        mock_upload = Mock(return_value={"secure_url": None})
        monkeypatch.setattr("app.services.users_service.cloudinary.uploader.upload", mock_upload)

        fake_image = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
        files = {"file": ("profile.jpg", fake_image, "image/jpeg")}

        response = await async_client.patch(
            f"{TEST_BASE_URL}/me/profile-photo",
            headers=auth_headers(test_listener_full.id, role="listener"),
            files=files,
        )

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.json() == {
            "detail": "Error al guardar la foto de perfil",
            "instance": "/me/profile-photo",
            "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "title": "File Upload Error",
            "type": "about:blank"
        }

    async def test_update_profile_photo_no_file(self, async_client: AsyncClient, test_listener_full: TestUser, monkeypatch: pytest.MonkeyPatch) -> None:
        """Reject request without file."""

        mock_upload = Mock(return_value={"secure_url": "https://example.com/photo.jpg"})
        monkeypatch.setattr("app.services.users_service.cloudinary.uploader.upload", mock_upload)

        response = await async_client.patch(
            f"{TEST_BASE_URL}/me/profile-photo",
            headers=auth_headers(test_listener_full.id, role="listener"),
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        mock_upload.assert_not_called()
