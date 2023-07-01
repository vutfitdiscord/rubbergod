from __future__ import annotations

from datetime import datetime
from typing import List

from sqlalchemy import BigInteger, Boolean, Column, DateTime, Interval, String

from database import database, session


class TimeoutDB(database.base):
    __tablename__ = "timeout"

    user_id = Column(BigInteger, primary_key=True)
    mod_id = Column(BigInteger)
    start = Column(DateTime)
    end = Column(DateTime)
    length = Column(Interval)
    reason = Column(String)
    isself = Column(Boolean)

    @classmethod
    def get_timeout_users(cls) -> List[TimeoutDB]:
        return session.query(cls).all()

    @classmethod
    def get_timeout_users_filter_self(cls, isself: bool = False) -> List[TimeoutDB]:
        return session.query(cls).filter(cls.isself == isself).all()

    @classmethod
    def get_timeout_user(cls, user_id: int) -> TimeoutDB:
        return session.query(cls).get(user_id)

    @classmethod
    def add_timeout(
        cls,
        user_id: int,
        mod_id: int,
        start: datetime,
        end: datetime,
        reason: str,
        isself: bool = False
    ) -> None:
        """
        Add the user and their timeout/selftimeout to the database.
        Save all datetimes in the database without timezone information.
        """
        exists = cls.get_timeout_user(user_id)
        if exists:
            exists.mod_id = mod_id
            exists.start = start
            exists.end = end
            exists.length = end - start
            exists.reason = reason
            exists.isself = isself
            session.commit()
            return
        timeout = cls(
            user_id=user_id,
            mod_id=mod_id,
            start=start,
            end=end,
            length=end-start,
            reason=reason,
            isself=isself
        )
        session.add(timeout)
        session.commit()

    @classmethod
    def remove_timeout(cls, user_id: int) -> None:
        user = cls.get_timeout_user(user_id)
        if user is None:
            return

        session.delete(user)
        session.commit()
