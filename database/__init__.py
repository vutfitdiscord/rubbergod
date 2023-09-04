from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from config.app_config import config


class Database():
    def __init__(self):
        self.base = declarative_base()
        self.db = create_engine(config.db_string)


database = Database()
session = sessionmaker(database.db)()
