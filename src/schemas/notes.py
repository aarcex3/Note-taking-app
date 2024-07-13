from datetime import datetime

from pydantic import BaseModel


class CreateNoteSchema(BaseModel):
  title:str
  content:str



class UpdateNoteSchema(BaseModel):
  title:str
  content:str
