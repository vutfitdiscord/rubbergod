from sqlalchemy import Column, Integer, String
from repository.database import database


class MemeRepost(database.base):
    __tablename__ = "bot_meme_reposts"

    original_message_id = Column(Integer, primary_key=True, nullable=False, unique=True)
    author_id = Column(Integer, nullable=False)
    reposted_message_id = Column(Integer, nullable=False)
    secondary_repost_message_id = Column(Integer, nullable=True)
