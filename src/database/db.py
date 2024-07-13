from sqlmodel import Session, SQLModel, create_engine

from src.config.cfg import SETTINGS

_engine = create_engine( f"sqlite:///{SETTINGS.DB_URL}", echo=True)

def create_db_and_tables():
  SQLModel.metadata.create_all(_engine)

def get_session():
  with Session(_engine) as session:
    yield session
