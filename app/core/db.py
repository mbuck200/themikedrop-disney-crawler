from sqlmodel import SQLModel, create_engine, Session
from .settings import Settings

def get_engine(settings: Settings):
    connect_args = {}
    if settings.db_url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
    engine = create_engine(settings.db_url, connect_args=connect_args, echo=False)
    return engine

def init_db(engine):
    SQLModel.metadata.create_all(engine)

def get_session(engine):
    return Session(engine)
