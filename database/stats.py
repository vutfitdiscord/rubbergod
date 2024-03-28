from __future__ import annotations

from typing import Optional

from sqlalchemy import Column, DateTime, ForeignKeyConstraint, Integer, PrimaryKeyConstraint, String, Text

from database import database, session


class Event(database.base):  # type: ignore
    __tablename__ = "stats_event"
    # events are shared between the cogs, so constraint key is needed here
    __table_args__ = (PrimaryKeyConstraint("name", "cog", name="id"),)

    name = Column(String)  # command or event name
    cog = Column(String)  # can be cog or event in button, select etc.

    @classmethod
    def get(cls, name: str, cog: str) -> Optional[Event]:
        return session.query(cls).filter(cls.name == name, cls.cog == cog).one_or_none()

    @classmethod
    def get_set(cls, name: str, cog: str) -> Event:
        event = cls.get(name, cog)
        if not event:
            event = cls(name=name, cog=cog)
            session.merge(event)
            session.commit()
        return event


class ErrorEvent(database.base):  # type: ignore
    __tablename__ = "stats_error_event"
    _table_args__ = (
        ForeignKeyConstraint(
            ["event_name", "cog"],
            ["stats_event.name", "stats_event.cog"],
            ondelete="CASCADE",
            onupdate="CASCADE",
        ),
    )

    id = Column(Integer, primary_key=True)
    event_name = Column(String, nullable=False)
    cog = Column(String, nullable=False)
    datetime = Column(DateTime)
    user_id = Column(String)
    args = Column(String)
    exception = Column(String)
    traceback = Column(Text)

    @classmethod
    def log(
        cls,
        event_name: str,
        cog: str,
        datetime,
        user_id: str,
        args: str,
        exception: str,
        traceback: str,
    ) -> ErrorEvent:
        Event.get_set(event_name, cog)
        error = cls(
            event_name=event_name,
            cog=cog,
            datetime=datetime,
            user_id=user_id,
            args=args,
            exception=exception,
            traceback=traceback,
        )
        error = session.merge(error)
        session.commit()
        return error

    @classmethod
    def get_traceback(cls, id: int) -> ErrorEvent:
        return session.query(cls).filter(cls.id == id).one_or_none()


# TODO: add new table that will log command usage
# class UsageEvent(database.base):
#     __tablename__ = 'stats_usage_event'
