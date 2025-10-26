from datetime import datetime, timezone, timedelta
from uuid import UUID
from jose import jwt

from app.core.config import settings


def _access_token(user_id: UUID, role: str) -> str:
    """Generate an access token for the test user with given role."""
    return jwt.encode(
        {
            "user_id": str(user_id),
            "role": role,
            "status": "active",
            "iat": int(datetime.now(timezone.utc).timestamp()),
            "exp": int((datetime.now(timezone.utc) + timedelta(minutes=30)).timestamp()),
            "iss": settings.AUTH_ISSUER,
            "type": "access",
        },
        settings.AUTH_SECRET,
        algorithm=settings.AUTH_ALGORITHM,
    )


def auth_headers(user_id: UUID, role: str) -> dict[str, str]:
    """Authentication headers for the test user."""
    return {"Authorization": f"Bearer {_access_token(user_id, role)}"}
