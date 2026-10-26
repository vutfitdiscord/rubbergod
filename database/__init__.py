from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from config.app_config import config


class Database:
    def __init__(self):
        self.base = declarative_base()
        db_string = config.db_string
        if db_string.startswith("postgresql+psycopg2://"):
            db_string = db_string.replace("postgresql+psycopg2://", "postgresql+psycopg://", 1)
        elif db_string.startswith("postgresql://"):
            db_string = db_string.replace("postgresql://", "postgresql+psycopg://", 1)
        self.db = create_engine(db_string, echo=False)


database = Database()
session = sessionmaker(database.db)()
