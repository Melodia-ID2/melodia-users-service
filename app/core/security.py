from typing import Any
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt, exceptions
from app.core.config import settings


security = HTTPBearer(auto_error=False)


def _verify_jwt(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            settings.AUTH_SECRET,
            algorithms=[settings.AUTH_ALGORITHM],
            issuer=settings.AUTH_ISSUER,
            options={
                "require_exp": True,
                "require_iat": True,
                "require_iss": True,
                "verify_aud": False,
                "leeway": 5,
            },
        )
        return payload
    except exceptions.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except exceptions.JWTClaimsError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token claims: {str(e)}")
    except exceptions.JWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")


def get_jwt_payload(
    creds: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict[str, Any]:
    if (
        creds is None
        or (creds.scheme or "").lower() != "bearer"
        or not creds.credentials
    ):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    token = creds.credentials
    return _verify_jwt(token)


def require_admin(payload: dict[str, Any] = Depends(get_jwt_payload)) -> dict[str, Any]:
    if payload.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return payload


def get_current_user_id(payload: dict[str, Any] = Depends(get_jwt_payload)) -> str:
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token: user_id missing")
    return user_id
