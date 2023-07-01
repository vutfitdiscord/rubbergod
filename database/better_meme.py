from __future__ import annotations

from typing import List, Optional

from sqlalchemy import Column, Integer, String

from database import database, session


class BetterMemeDB(database.base):
    __tablename__ = 'bot_better_meme'

    member_ID = Column(String, primary_key=True)
    posts = Column(Integer, default=0)
    total_karma = Column(Integer, default=0)

    @classmethod
    def get_member(cls, user_id: int) -> Optional[BetterMemeDB]:
        return session.query(cls).filter(cls.member_ID == str(user_id)).one_or_none()

    @classmethod
    def add_post_to_repo(cls, user_id: int, karma: int) -> None:
        member = cls.get_member(user_id)
        if member is not None:
            member.total_karma += karma
            member.posts += 1
            session.merge(member)
            session.commit()
        else:
            session.add(cls(member_ID=str(user_id), posts=1, total_karma=karma))
            session.commit()

    @classmethod
    def update_post_karma(cls, user_id: int, karma: int) -> None:
        member = cls.get_member(user_id)
        if member is not None:
            member.total_karma += karma
            session.merge(member)
            session.commit()

    @classmethod
    def get_leaderboard(cls, order_by: str) -> List[BetterMemeDB]:
        return session.query(cls).order_by(getattr(cls, order_by).desc())
