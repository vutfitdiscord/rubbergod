from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import BigInteger, Boolean, Column, DateTime, ForeignKey, String
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship

import utils
from database import database, session


class TimeoutDB(database.base):  # type: ignore
    __tablename__ = "timeout"

    id = Column(BigInteger, primary_key=True)
    mod_id = Column(String)  # For automod this value is 1
    start = Column(DateTime)  # in UTC
    end = Column(DateTime)  # in UTC
    reason = Column(String)
    guild_id = Column(String)
    isself = Column(Boolean, default=False)
    user: Mapped[TimeoutUserDB] = relationship(back_populates="timeouts")
    user_id: Mapped[String] = mapped_column(ForeignKey("timeout_user.id"))

    @hybrid_property
    def is_active(self) -> bool:
        now = datetime.now(timezone.utc).replace(tzinfo=None)  # can't compare timezone aware and unaware
        return self.end > now

    @hybrid_property
    def length(self) -> timedelta:
        return self.end - self.start

    @property
    def start_end_local(self) -> tuple[datetime, datetime]:
        """Return the start and end time in the local timezone.
        First we need to add UTC timezone then convert it to local timezone.
        """
        start = self.start.replace(tzinfo=timezone.utc).astimezone(utils.general.get_local_zone())
        end = self.end.replace(tzinfo=timezone.utc).astimezone(utils.general.get_local_zone())
        return start, end

    @classmethod
    def add_timeout(
        cls,
        user_id: str,
        mod_id: str,
        start: datetime,
        end: datetime,
        reason: str,
        guild_id: str,
        isself: bool = False,
    ) -> TimeoutDB:
        """Add the user and their timeout/selftimeout to the database."""
        user = TimeoutUserDB.get_user(user_id)
        timeout = TimeoutUserDB.get_active_timeout(user_id)

        if user and timeout:
            # if user has already timeout update it
            cls.update_timeout(timeout, mod_id, end, reason)
            return timeout

        if user is None:
            TimeoutUserDB.add_user(user_id)

        timeout = cls(
            user_id=str(user_id),
            mod_id=str(mod_id),
            start=start,
            end=end,
            reason=reason,
            guild_id=guild_id,
            isself=isself,
        )

        session.add(timeout)
        session.commit()
        return timeout

    @classmethod
    def update_timeout(
        cls,
        timeout: TimeoutDB,
        mod_id: str,
        end: datetime,
        reason: str,
    ) -> None:
        """Update the timeout if user has already timeout."""
        timeout.mod_id = mod_id
        timeout.end = end
        timeout.reason = reason
        session.commit()

    @classmethod
    def get_timeout_user(cls, user_id: str) -> TimeoutDB:
        return session.query(TimeoutDB).get(str(user_id))

    @classmethod
    def remove_timeout(cls, user_id: str, permanent: bool = False) -> TimeoutDB | None:
        timeout = TimeoutUserDB.get_active_timeout(str(user_id))
        if timeout is None:
            return None

        if permanent:
            session.delete(timeout)
        else:
            timeout.end = datetime.now(timezone.utc)
        session.commit()
        return timeout


class TimeoutUserDB(database.base):  # type: ignore
    __tablename__ = "timeout_user"

    id = Column(String, primary_key=True)
    timeouts: Mapped[list[TimeoutDB]] = relationship(back_populates="user")

    @hybrid_property
    def timeout_count(self) -> int:
        return session.query(TimeoutDB).filter_by(user_id=self.id, isself=False).count()

    @classmethod
    def add_user(cls, user_id: str) -> None:
        user = cls(id=str(user_id))
        session.add(user)
        session.commit()

    @classmethod
    def get_user(cls, user_id: str) -> TimeoutUserDB:
        return session.query(cls).get(str(user_id))

    @classmethod
    def get_active_timeouts(cls, isself: bool = False) -> list[TimeoutDB]:
        return session.query(TimeoutDB).filter_by(isself=isself, is_active=True).all()

    @classmethod
    def get_active_timeout(cls, user_id: str) -> TimeoutDB | None:
        return session.query(TimeoutDB).filter_by(user_id=str(user_id), is_active=True).first()

    def get_all_timeouts(self, isself: bool = False, descending: bool = True) -> list[TimeoutDB]:
        if descending:
            timeouts_query = session.query(TimeoutDB).filter_by(user_id=self.id, isself=isself)
            return timeouts_query.order_by(TimeoutDB.start.desc()).all()

        timeouts_query = session.query(TimeoutDB).filter_by(user_id=self.id, isself=isself)
        return timeouts_query.order_by(TimeoutDB.start.asc()).all()

    def get_last_timeout(self, isself: bool = False) -> TimeoutDB | None:
        return (
            session.query(TimeoutDB)
            .filter_by(user_id=self.id, isself=isself)
            .order_by(TimeoutDB.start.desc())
            .first()
        )
