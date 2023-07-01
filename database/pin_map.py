from __future__ import annotations

from typing import List

from sqlalchemy import Column, String

from database import database, session


class PinMapDB(database.base):
    __tablename__ = 'bot_pin_map'

    channel_id = Column(String, primary_key=True)
    message_id = Column(String)

    @classmethod
    def find_channel_by_id(cls, channel_id: str) -> PinMapDB:
        return session.query(cls).filter(cls.channel_id == channel_id).one_or_none()

    @classmethod
    def add_or_update_channel(cls, channel_id: str, message_id: str) -> None:
        item: cls = cls.find_channel_by_id(channel_id)

        if item is None:
            item = cls(channel_id=channel_id, message_id=message_id)
            session.add(item)
        else:
            item.message_id = message_id

        session.commit()

    @classmethod
    def remove_channel(cls, channel_id: str) -> None:
        session.query(cls).filter(cls.channel_id == channel_id).delete()
        session.commit()

    @classmethod
    def get_mappings(cls) -> List[PinMapDB]:
        return list(session.query(cls).all())
