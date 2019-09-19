from sqlalchemy.ext.declarative import declarative_base
from repository.base_repository import BaseRepository
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


class Database(BaseRepository):
    def __init__(self):
        super().__init__()
        self.base = declarative_base()
        self.db = create_engine(self.config.db_string)


database = Database()
session = sessionmaker(database.db)()
