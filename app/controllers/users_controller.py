from fastapi import Depends, Request
from sqlmodel import Session

from app.core.database import get_session
from app.services.users_service import UsersService


class UsersController:
    def __init__(self, service: UsersService):
        self.service = service

    def get_all_users(self, req: Request, session: Session = Depends(get_session)):
        return self.service.get_all_users(session=session)
