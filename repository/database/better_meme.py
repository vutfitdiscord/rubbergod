from sqlalchemy import Column, Integer, String

from repository.database import database


class BetterMeme(database.base):
    __tablename__ = 'bot_better_meme'

    member_ID = Column(String, primary_key=True)
    posts = Column(Integer, default=0)
    total_karma = Column(Integer, default=0)
