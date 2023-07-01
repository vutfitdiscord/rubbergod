from __future__ import annotations

import datetime
from typing import Optional

from sqlalchemy import Column, Date, Integer

from database import database, session


class ErrorLog(database.base):
    __tablename__ = "bot_error_log"

    id = Column(Integer, primary_key=True)
    date = Column(Date)

    @classmethod
    def set(cls) -> bool:
        """Set new date of last error.
        :return: Whether the date got updated or not.
        """
        query = cls.get()
        today = datetime.date.today()
        if getattr(query, "date", None) == today:
            return False

        if query is None:
            query = cls()
            session.add(query)
        query.date = today
        session.commit()
        return True

    @classmethod
    def get(cls) -> Optional[ErrorLog]:
        return session.query(cls).one_or_none()
