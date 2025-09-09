from fastapi import APIRouter, Depends
from app.controllers.users_controller import UsersController
from app.services.users_service import UsersService
from app.repositories.users_repository import UsersRepository
from sqlmodel import Session
from app.core.database import get_session
from app.core.security import require_admin

router = APIRouter(prefix="/users", tags=["users"])
users_repository = UsersRepository()
users_service = UsersService(repository=users_repository)
users_controller = UsersController(service=users_service)


@router.get("/")
def get_all_users(
    session: Session = Depends(get_session), _: None = Depends(require_admin)
):
    return users_controller.get_all_users(session=session)
