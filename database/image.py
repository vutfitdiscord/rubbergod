# stolen from rubbergoddess
from __future__ import annotations

from datetime import datetime
from typing import List

from sqlalchemy import BigInteger, Column, DateTime, String
from sqlalchemy.orm import Query

from database import database, session


class ImageDB(database.base):
    __tablename__ = "images"

    attachment_id = Column(BigInteger, primary_key=True)
    message_id = Column(BigInteger)
    channel_id = Column(BigInteger)
    timestamp = Column(DateTime)
    dhash = Column(String)

    @classmethod
    def add_image(cls, channel_id: int, message_id: int, attachment_id: int, dhash: str) -> None:
        """Add new image hash"""

        if cls.getByMessage(message_id) is not None:
            # message already indexed
            return

        session.add(
            cls(
                channel_id=channel_id,
                message_id=message_id,
                attachment_id=attachment_id,
                dhash=dhash,
                timestamp=datetime.now().replace(microsecond=0),
            )
        )
        session.commit()

    @classmethod
    def getHash(cls, dhash: str) -> List[ImageDB]:
        return session.query(cls).filter(cls.dhash == dhash).all()

    @classmethod
    def getByMessage(cls, message_id: int) -> ImageDB:
        return session.query(cls).filter(cls.message_id == message_id).one_or_none()

    @classmethod
    def getAll(cls) -> Query:
        return session.query(cls)

    @classmethod
    def getLast(cls, num: int) -> Query:
        return session.query(cls)[:num]

    @classmethod
    def deleteByMessage(cls, message_id: int) -> int:
        i = session.query(cls).filter(cls.message_id == message_id).delete()
        session.commit()
        return i
