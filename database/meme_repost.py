from __future__ import annotations

from typing import Optional

from sqlalchemy import Column, String

from database import database, session


class MemeRepostDB(database.base):
    __tablename__ = "bot_meme_reposts"

    original_message_id = Column(String, primary_key=True, nullable=False, unique=True)
    author_id = Column(String, nullable=False)
    reposted_message_id = Column(String, nullable=False)
    secondary_repost_message_id = Column(String, nullable=True)

    @classmethod
    def find_repost_by_original_message_id(cls, message_id: str) -> Optional[MemeRepostDB]:
        return session.query(cls).filter(
            cls.original_message_id == str(message_id)).one_or_none()

    @classmethod
    def find_repost_by_repost_message_id(cls, message_id: str) -> Optional[MemeRepostDB]:
        return session.query(cls).filter(
            (cls.reposted_message_id == str(message_id)) |
            (cls.secondary_repost_message_id == str(message_id))).one_or_none()

    @classmethod
    def create_repost(
        cls,
        original_message_id: int,
        repost_message_id: int,
        author_id: int,
        secondary_repost_message_id: int = None
    ) -> None:
        item = cls(
            original_message_id=str(original_message_id),
            reposted_message_id=str(repost_message_id),
            author_id=str(author_id),
            secondary_repost_message_id=str(secondary_repost_message_id)
        )
        session.add(item)
        session.commit()
