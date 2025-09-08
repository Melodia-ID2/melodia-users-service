from pydantic import BaseModel
import os


class Settings(BaseModel):
    DATABASE_USER: str = os.getenv("DATABASE_USER", "postgres")
    DATABASE_PASSWORD: str = os.getenv("DATABASE_PASSWORD", "postgres")
    DATABASE_HOST: str = os.getenv("DATABASE_HOST", "localhost")
    DATABASE_PORT: str = os.getenv("DATABASE_PORT", "5432")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "app")
    DATABASE_URL: str = f"postgresql+psycopg://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"
    AUTH_SECRET: str = os.getenv("AUTH_SECRET", "dev-secret")
    AUTH_ISSUER: str = os.getenv("AUTH_ISSUER", "auth-service")


settings = Settings()
