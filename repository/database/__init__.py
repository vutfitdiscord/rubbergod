from sqlalchemy.ext.declarative import declarative_base
from repository.base_repository import BaseRepository
from sqlalchemy.orm import sessionmaker


class Database(BaseRepository):
    def __init__(self):
        super().__init__()
        self.base = declarative_base()


database = Database()
session = sessionmaker(database.db)()
