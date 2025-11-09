from uuid import UUID

from sqlmodel import Field, SQLModel


class UserMutedArtist(SQLModel, table=True):
    user_id: UUID = Field(foreign_key="useraccount.id", ondelete="CASCADE", primary_key=True, index=True, nullable=False)
    artist_id: UUID = Field(foreign_key="useraccount.id", ondelete="CASCADE", primary_key=True, index=True, nullable=False)
