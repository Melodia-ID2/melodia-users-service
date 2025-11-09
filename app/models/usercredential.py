from uuid import UUID

from sqlmodel import Field, SQLModel


class UserCredential(SQLModel, table=True):
    email: str = Field(primary_key=True)
    provider: str = Field(primary_key=True, default="local")
    password: str | None = Field(default=None)
    provider_id: str | None = Field(default=None)
    user_id: UUID = Field(foreign_key="useraccount.id", ondelete="CASCADE", index=True)
