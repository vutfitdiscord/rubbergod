from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from repository.base_repository import BaseRepository


class Database(BaseRepository):
    def __init__(self):
        super().__init__()
        self.base = declarative_base()
        self.db = create_engine(self.config.db_string)


database = Database()
session = sessionmaker(database.db)()
