from sqlmodel import Session

from app.services.users_service import UsersService


class UsersController:
    def __init__(self, service: UsersService):
        self.service = service

    def get_all_users(self, session: Session):
        return self.service.get_all_users(session=session)
