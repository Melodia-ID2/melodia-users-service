from sqlmodel import Session, SQLModel, create_engine

from app.core.config import settings

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True,connect_args={"prepare_threshold": None})

def get_session():
    with Session(engine) as session:
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise


def init_db():
    SQLModel.metadata.create_all(engine)
