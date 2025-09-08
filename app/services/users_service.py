from sqlmodel import Session


class UsersService:
    def __init__(self, repository):
        self.repository = repository

    def get_all_users(self, session: Session):
        return self.repository.get_all_users(session=session)
