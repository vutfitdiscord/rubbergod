from __future__ import annotations

from datetime import date
from enum import IntEnum

from sqlalchemy import Column, Date, Integer

from database import database, session


class ErrorRow(IntEnum):
    """Enum for error log rows. Represents ids in the database."""

    last_error = 1
    start_streak = 2
    end_streak = 3


class ErrorLogDB(database.base):  # type: ignore
    """Database model for error log.

    Always has 3 rows:
    - `last_error` - date of the last error
    - `start_streak` - start date of the longest streak
    - `end_streak` - end date of the longest streak
    """

    __tablename__ = "bot_error_log"

    id = Column(Integer, primary_key=True)
    date = Column(Date, default=date.today())

    @classmethod
    def init(cls) -> None:
        """Initialize database with default rows."""
        if session.query(cls).count():
            # If the table is not empty do not initialize
            return

        last_error = cls(id=ErrorRow.last_error)
        start_streak = cls(id=ErrorRow.start_streak)
        end_streak = cls(id=ErrorRow.end_streak)
        for error in [last_error, start_streak, end_streak]:
            session.add(error)

        session.commit()
        return

    @classmethod
    def get(cls, id: ErrorRow) -> ErrorLogDB:
        return session.query(cls).get(id)

    @classmethod
    def set(cls) -> None:
        """Set new date of last error."""
        last_error, start_streak, end_streak = cls.get_all()
        today = date.today()

        if getattr(last_error, "date", None) == today:
            return

        current_streak = today - last_error.date
        longest_streak = end_streak.date - start_streak.date

        if current_streak > longest_streak:
            start_streak.date = last_error.date
            end_streak.date = today

        last_error.date = today
        session.commit()
        return

    @classmethod
    def days_without_error(cls) -> int:
        last_error = cls.get(ErrorRow.last_error)
        today = date.today()
        return (today - last_error.date).days

    @classmethod
    def get_all(cls) -> tuple[ErrorLogDB, ErrorLogDB, ErrorLogDB]:
        last_error = cls.get(ErrorRow.last_error)
        start_streak = cls.get(ErrorRow.start_streak)
        end_streak = cls.get(ErrorRow.end_streak)
        return last_error, start_streak, end_streak  # type: ignore

    @classmethod
    def get_longest_streak(cls) -> tuple[Date, Date]:
        last_error, start_streak, end_streak = cls.get_all()
        today = date.today()

        current_streak = today - last_error.date
        longest_streak = end_streak.date - start_streak.date

        if current_streak > longest_streak:
            start_streak.date = last_error.date
            end_streak.date = today
            session.commit()

        return start_streak.date, end_streak.date
