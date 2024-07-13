from datetime import datetime, timezone

from pydantic.types import UUID4
from sqlmodel import Field, SQLModel
from sqlmodel.main import Relationship

from src.models.user import UserModel


class NoteModel(SQLModel, table=True):
    id: UUID4 = Field(default=None, primary_key=True)
    title: str = Field(default=None, unique=True)
    content: str
    created_at: str = Field(default=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"))
    updated_at: str = Field(default=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"))
    owner_id:UUID4 = Field(default=None, foreign_key="usermodel.id")
    owner: UserModel | None = Relationship(back_populates='notes')

