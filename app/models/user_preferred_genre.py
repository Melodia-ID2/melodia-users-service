from uuid import UUID

from sqlmodel import Field, SQLModel


class UserPreferredGenre(SQLModel, table=True):
    user_id: UUID = Field(foreign_key="useraccount.id", ondelete="CASCADE", primary_key=True, index=True, nullable=False)
    genre_code: str = Field(max_length=20, primary_key=True, nullable=False)
