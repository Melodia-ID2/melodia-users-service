from sqlmodel import SQLModel, Session, create_engine

from app.core.config import settings

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)


def get_session():
    with Session(engine) as session:
        yield session

def init_db():
    from app.models.user import User

    SQLModel.metadata.create_all(engine)
