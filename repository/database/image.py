# stolen from rubbergoddess
from sqlalchemy import Column, String, BigInteger, DateTime
from repository.database import database


class Image(database.base):
    __tablename__ = "images"

    attachment_id = Column(BigInteger, primary_key=True)
    message_id    = Column(BigInteger)
    channel_id    = Column(BigInteger)
    timestamp     = Column(DateTime)
    dhash         = Column(String)
