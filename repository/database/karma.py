from sqlalchemy import Column, String, Integer
from repository.database import database


class Karma(database.base):
    __tablename__ = 'bot_karma'

    member_ID = Column(String, primary_key=True)
    karma = Column(Integer)
    positive = Column(Integer)
    negative = Column(Integer)


class Karma_emoji(database.base):
    __tablename__ = 'bot_karma_emoji'
    emoji_ID = Column(String, primary_key=True)
    value = Column(Integer)
