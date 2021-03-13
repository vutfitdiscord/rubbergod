from sqlalchemy import Column, BigInteger, DateTime, Boolean

from repository.database import database


class Vote(database.base):
    __tablename__ = 'bot_votes'

    message_id = Column(BigInteger, primary_key=True)
    channel_id = Column(BigInteger, nullable=False)
    ends_at = Column(DateTime, nullable=True)
    is_one_of = Column(Boolean, default=False, nullable=False)
