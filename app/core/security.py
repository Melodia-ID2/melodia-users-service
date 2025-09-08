from fastapi import Depends, Header, HTTPException, status
from jose import jwt, exceptions
from app.core.config import settings


def _parse_bearer_token(authorization: str | None) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header",
        )
    return authorization.split(" ", 1)[1]


def _verify_jwt(token: str) -> dict[str, str]:
    try:
        payload = jwt.decode(
            token,
            settings.AUTH_SECRET,
            algorithms=["HS256"],
            issuer=settings.AUTH_ISSUER,
            options={"require": ["exp", "iat", "iss"]},
        )
        return payload
    except exceptions.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except exceptions.JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")


def get_jwt_payload(
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> dict[str, str]:
    token = _parse_bearer_token(authorization)
    payload = _verify_jwt(token)
    return payload


def require_admin(payload: dict[str, str] = Depends(get_jwt_payload)) -> dict[str, str]:
    if payload.get("role") != "admin":
        raise HTTPException(status_code=403, detail="forbidden")
    return payload
