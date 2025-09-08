from sqlmodel import Session, select

from app.models.user import User


class UsersRepository:
    def get_all_users(self, session: Session):
        return session.exec(select(User)).all()
