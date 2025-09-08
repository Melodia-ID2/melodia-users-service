from sqlmodel import Session
from app.repositories.users_repository import UsersRepository


class UsersService:
    def __init__(self, repository: UsersRepository):
        self.repository = repository

    def get_all_users(self, session: Session):
        return self.repository.get_all_users(session=session)
