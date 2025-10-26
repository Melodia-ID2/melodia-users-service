from typing import Any

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import exceptions, jwt
from sqlmodel import Session

from app.core.config import settings
from app.core.database import get_session
from app.errors.exceptions import AuthenticationError, NotFoundError
from app.repositories import users_repository as user_repo

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
        raise AuthenticationError("El token ha expirado")
    except exceptions.JWTClaimsError as e:
        raise AuthenticationError(f"Token invalido 'claims': {str(e)}")
    except exceptions.JWTError as e:
        raise AuthenticationError(f"Token invalido: {str(e)}")


def get_jwt_payload(
    creds: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict[str, Any]:
    if creds is None or (creds.scheme or "").lower() != "bearer" or not creds.credentials:
        raise AuthenticationError("Token de autenticación invalido o no proporcionado")
    token = creds.credentials
    return _verify_jwt(token)


def require_admin(payload: dict[str, Any] = Depends(get_jwt_payload)) -> dict[str, Any]:
    if payload.get("role") != "admin":
        raise AuthenticationError("Se requiere privilegios de administrador")
    return payload


def get_current_user_id(payload: dict[str, Any] = Depends(get_jwt_payload), session: Session = Depends(get_session)) -> str:
    user_id = payload.get("user_id")
    if not user_id:
        raise AuthenticationError("ID de usuario no encontrado en el token")
    user = user_repo.get_account_by_id(session, user_id)
    if not user:
        raise NotFoundError("Usuario no encontrado")
    if user.status != "active":
        raise AuthenticationError("El usuario está bloqueado")
    if payload.get("role") != user.role:
        raise AuthenticationError("El rol del usuario no coincide con el del token")

    return user_id
