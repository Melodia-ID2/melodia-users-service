from pydantic import BaseModel
import os


class Settings(BaseModel):
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/app"
    )


settings = Settings()
