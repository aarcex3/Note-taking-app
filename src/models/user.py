from pydantic.types import UUID4
from sqlmodel import Field, SQLModel
from sqlmodel.main import Relationship


class UserModel(SQLModel, table=True):
    id: UUID4 = Field(default=None, primary_key=True)
    username: str = Field(default=None, unique=True)
    email: str = Field(default=None, unique=True)
    password: str
    notes: list['NoteModel'] = Relationship(back_populates='owner')
