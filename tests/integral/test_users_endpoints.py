# import uuid
# from datetime import datetime

# import pytest
# from sqlalchemy.ext.asyncio import AsyncSession

# from app.schemas.user import UserProfileCreate, UserProfileUpdate

# BASE_URL = "http://localhost:8002"

# @pytest.mark.asyncio
# class TestUserEndpoints:
#     async def test_get_me_authenticated(self, test_client, auth_headers):
#         response = await test_client.get(f"{BASE_URL}/me", headers=auth_headers)
#         assert response.status_code == 200
#         data = response.json()
#         assert "id" in data
#         assert "username" in data
#         assert "email" in data

#     async def test_update_me(self, test_client, auth_headers):
#         update_data = {
#             "first_name": "Updated",
#             "last_name": "User",
#             "bio": "Updated bio"
#         }
#         response = await test_client.put(
#             f"{BASE_URL}/me",
#             json=update_data,
#             headers=auth_headers
#         )
#         assert response.status_code == 200
#         data = response.json()
#         assert data["first_name"] == "Updated"
#         assert data["last_name"] == "User"
#         assert data["bio"] == "Updated bio"

#     async def test_search_users(self, test_client, auth_headers):
#         # First, create some test users
#         test_users = [
#             {"username": f"testuser_{i}", "email": f"test{i}@example.com", "password": "testpass123"}
#             for i in range(3)
#         ]
        
#         for user in test_users:
#             await test_client.post(
#                 f"{BASE_URL}/auth/register",
#                 json=user
#             )
        
#         # Test search
#         response = await test_client.get(
#             f"{BASE_URL}/search?query=testuser",
#             headers=auth_headers
#         )
#         assert response.status_code == 200
#         data = response.json()
#         assert len(data["items"]) >= 3

#     async def test_create_user_profile(self, test_client, auth_headers):
#         profile_data = {
#             "first_name": "Test",
#             "last_name": "User",
#             "bio": "Test bio",
#             "birth_date": "1990-01-01",
#             "country": "Test Country",
#             "city": "Test City"
#         }
#         response = await test_client.post(
#             f"{BASE_URL}/profile",
#             json=profile_data,
#             headers=auth_headers
#         )
#         assert response.status_code == 201
#         data = response.json()
#         assert data["first_name"] == "Test"
#         assert data["last_name"] == "User"

#     async def test_view_user_profile(self, test_client, auth_headers, test_user_id):
#         response = await test_client.get(
#             f"{BASE_URL}/{test_user_id}/profile",
#             headers=auth_headers
#         )
#         assert response.status_code == 200
#         data = response.json()
#         assert "id" in data
#         assert "username" in data
#         assert "bio" in data

#     async def test_follow_user(self, test_client, auth_headers, test_user_id, another_test_user_id):
#         # Follow user
#         response = await test_client.post(
#             f"{BASE_URL}/{another_test_user_id}/follow",
#             headers=auth_headers
#         )
#         assert response.status_code == 200
        
#         # Check following list
#         response = await test_client.get(
#             f"{BASE_URL}/{test_user_id}/following",
#             headers=auth_headers
#         )
#         assert response.status_code == 200
#         data = response.json()
#         assert any(user["id"] == str(another_test_user_id) for user in data["items"])
        
#         # Check followers list
#         response = await test_client.get(
#             f"{BASE_URL}/{another_test_user_id}/followers",
#             headers=auth_headers
#         )
#         assert response.status_code == 200
#         data = response.json()
#         assert any(user["id"] == str(test_user_id) for user in data["items"])

#     async def test_upload_profile_picture(self, test_client, auth_headers, test_image):
#         with open(test_image, "rb") as f:
#             response = await test_client.post(
#                 f"{BASE_URL}/photo-profile",
#                 files={"file": ("test.jpg", f, "image/jpeg")},
#                 headers={"Authorization": auth_headers["Authorization"]}
#             )
#         assert response.status_code == 200
#         data = response.json()
#         assert "url" in data
#         assert data["url"].endswith(".jpg") or data["url"].endswith(".jpeg")
