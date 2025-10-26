from datetime import datetime, timezone, timedelta
from jose import jwt

from tests.integral.fixtures.factories import TestArtist, TestUser
from app.core.config import settings


def _access_token(user: TestUser | TestArtist, role: str) -> str:
    """Generate an access token for the test user with given role."""
    return jwt.encode(
        {
            "user_id": str(user.id),
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


def auth_headers(user: TestUser | TestArtist, role: str) -> dict[str, str]:
    """Headers de autenticación para el usuario de prueba."""
    return {"Authorization": f"Bearer {_access_token(user, role)}"}
