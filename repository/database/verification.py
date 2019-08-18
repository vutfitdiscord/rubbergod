from sqlalchemy import Column, String, Integer
from repository.database import database


class Permit(database.base):
    __tablename__ = 'bot_permit'

    login = Column(String, primary_key=True)
    discord_ID = Column(String)


class Valid_person(database.base):
    __tablename__ = 'bot_valid_persons'

    login = Column(String, primary_key=True)
    name = Column(String)
    year = Column(String)
    code = Column(String)
    status = Column(Integer, default=1)
