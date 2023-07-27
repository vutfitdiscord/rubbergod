from __future__ import annotations

from datetime import date
from enum import IntEnum
from typing import Optional

from sqlalchemy import Column, Date, Integer

from database import database, session


class ErrorRow(IntEnum):
    """Enum for error log rows. Represents ids in the database."""
    last_error = 1
    start_streak = 2
    end_streak = 3


class ErrorLogDB(database.base):
    __tablename__ = "bot_error_log"

    id = Column(Integer, primary_key=True)
    date = Column(Date, default=date.today())

    @classmethod
    def init(cls) -> None:
        """initialize database with default values"""
        last_error = cls(id=ErrorRow.last_error)
        start_streak = cls(id=ErrorRow.start_streak)
        end_streak = cls(id=ErrorRow.end_streak)
        for error in [last_error, start_streak, end_streak]:
            session.merge(error)
        session.commit()

    @classmethod
    def set(cls) -> bool:
        """Set new date of last error.
        :return: Whether the date got updated or not.
        """
        last_error, start_streak, end_streak = cls.get_all()
        today = date.today()

        if getattr(last_error, "date", None) == today:
            return False

        if any(error is None for error in [last_error, start_streak, end_streak]):
            cls.init()

        current_streak = today - last_error.date
        longest_streak = end_streak.date - start_streak.date

        if current_streak > longest_streak:
            start_streak.date = last_error.date
            end_streak.date = today

        last_error.date = today
        session.commit()
        return True

    @classmethod
    def get(cls, id) -> Optional[ErrorLogDB]:
        return session.query(cls).get(id)

    @classmethod
    def get_all(cls) -> tuple[Optional[ErrorLogDB], Optional[ErrorLogDB], Optional[ErrorLogDB]]:
        last_error = cls.get(ErrorRow.last_error)
        start_streak = cls.get(ErrorRow.start_streak)
        end_streak = cls.get(ErrorRow.end_streak)
        return last_error, start_streak, end_streak

    @classmethod
    def get_longest_streak(cls) -> int:
        last_error, start_streak, end_streak = cls.get_all()
        today = date.today()

        if any(error is None for error in [last_error, start_streak, end_streak]):
            cls.init()
            last_error, start_streak, end_streak = cls.get_all()

        current_streak = today - last_error.date
        longest_streak = end_streak.date - start_streak.date
        if current_streak > longest_streak:
            start_streak.date = last_error.date
            end_streak.date = today
            session.commit()

        return start_streak.date, end_streak.date
