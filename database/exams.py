from __future__ import annotations

from typing import List

from sqlalchemy import Column, String

from database import database, session


class ExamsTermsMessageDB(database.base):
    __tablename__ = "exams_terms_message"

    message_id = Column(String, primary_key=True)
    channel_id = Column(String, nullable=False, index=True)

    @classmethod
    def create_term_message(cls, message_id: str, channel_id: str) -> ExamsTermsMessageDB:
        item = cls(message_id=str(message_id), channel_id=str(channel_id))
        session.add(item)
        session.commit()
        return item

    @classmethod
    def get_message_from_channel(cls, channel_id: str) -> List[ExamsTermsMessageDB]:
        return session.query(cls).filter(cls.channel_id == str(channel_id)).all()

    @classmethod
    def remove_term_message(cls, message_id: str) -> None:
        session.query(cls).filter(cls.message_id == str(message_id)).delete()
        session.commit()

    @classmethod
    def remove_from_channel(cls, channel_id: str) -> List[int]:
        messages = cls.get_message_from_channel(channel_id)
        message_ids = [int(m.message_id) for m in messages]

        if message_ids:
            session.query(cls).filter(cls.channel_id == str(channel_id)).delete()
            session.commit()

        return message_ids
