from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy import BigInteger, Boolean, Column, DateTime
from sqlalchemy.sql.expression import or_

from database import database, session


class VoteDB(database.base):
    __tablename__ = 'bot_votes'

    message_id = Column(BigInteger, primary_key=True)
    channel_id = Column(BigInteger, nullable=False)
    ends_at = Column(DateTime, nullable=True)
    is_one_of = Column(Boolean, default=False, nullable=False)

    @classmethod
    def get_pending_votes(cls) -> List[VoteDB]:
        return session.query(VoteDB).filter(or_(VoteDB.ends_at is None, VoteDB.ends_at >= datetime.now()))

    @classmethod
    def add_vote(
        cls, message_id: int, channel_id: int, ends_at: Optional[datetime], is_one_of: bool = False
    ) -> None:
        vote = VoteDB(message_id=message_id, channel_id=channel_id, ends_at=ends_at, is_one_of=is_one_of)
        session.add(vote)
        session.commit()

    @classmethod
    def remove(cls, message_id: str) -> None:
        session.query(VoteDB).filter(VoteDB.message_id == message_id).delete()
        session.commit()
