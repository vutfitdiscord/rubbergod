from __future__ import annotations

from datetime import datetime, timezone
from enum import IntEnum

from sqlalchemy import (Boolean, Column, DateTime, ForeignKey, Integer, String,
                        UniqueConstraint)
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.expression import or_

from database import database, session


class VoterDB(database.base):
    __tablename__ = "voter"

    id = Column(String, primary_key=True)
    poll_option_id = Column(Integer, ForeignKey("poll_option.id"), nullable=False, primary_key=True)
    poll_option = relationship("PollOptionDB", back_populates="voters")

    @classmethod
    def add(cls, voter_id: str, poll_option_id: int) -> VoterDB:
        voter = cls(id=str(voter_id), poll_option_id=poll_option_id)
        session.add(voter)
        session.commit()
        return voter

    @classmethod
    def get(cls, voter_id: str, poll_option_id: int) -> VoterDB | None:
        return session.query(cls).get((str(voter_id), poll_option_id))


class PollType(IntEnum):
    """Enum for poll types."""
    basic = 1       # Basic is multiple choice poll with one or multiple votes per person
    boolean = 2     # Boolean is yes/no poll where you can only vote for one option
    opinion = 3     # Opinion is agree/neutral/disagree poll where you can only vote for one option


class PollDB(database.base):
    __tablename__ = "poll"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    author_id = Column(String, nullable=False)
    message_url = Column(String, nullable=False)
    poll_type = Column(Integer, nullable=False)
    start = Column(DateTime, nullable=False, default=datetime.now(timezone.utc))
    end = Column(DateTime)      # in UTC
    closed = Column(Boolean, nullable=True, default=False)
    closed_by = Column(String, nullable=True, default=None)
    closed_datetime = Column(DateTime, nullable=True, default=None)     # in UTC
    options: Mapped[list[PollOptionDB]] = relationship(back_populates="poll", cascade="all,delete")
    max_votes = Column(Integer, nullable=False)
    anonymous = Column(Boolean, nullable=False)

    @hybrid_property
    def is_active(self) -> bool:
        if self.closed:
            return False

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        return self.end > now

    @classmethod
    def add(
        cls,
        title: str,
        author_id: str,
        message_url: str,
        poll_type: PollType,
        end: datetime,
        anonymous: bool,
        poll_options: dict,
        max_votes: int = 1,
        **kwargs
    ) -> PollDB:
        new_poll = cls(
            title=title,
            author_id=author_id,
            message_url=message_url,
            poll_type=poll_type,
            end=end,
            anonymous=anonymous,
            max_votes=max_votes,
        )
        for emoji, option in poll_options.items():
            new_poll.options.append(PollOptionDB(emoji=emoji, text=option))
        session.add(new_poll)
        session.commit()
        return new_poll

    @classmethod
    def get(cls, poll_id: int) -> PollDB | None:
        return session.query(cls).get(poll_id)

    @classmethod
    def get_pending_polls(cls) -> list[PollDB]:
        return session.query(cls).filter(or_(cls.end is None, cls.end > datetime.now(timezone.utc)))

    @classmethod
    def get_pending_polls_by_type(cls, type: PollType) -> list[PollDB]:
        return cls.get_pending_polls().filter(cls.poll_type == type).all()

    @classmethod
    def get_author_id(cls, poll_id: int) -> str | None:
        poll = cls.get(poll_id)
        if not poll:
            return
        return poll.author_id

    def remove_voter(self, voter: VoterDB) -> None:
        for option in self.options:
            option.remove_voter(voter)
        session.commit()

    def add_voter(self, voter_id: str, poll_option_id: int) -> None:
        if self.max_votes == 1:
            for option in self.options:
                option.remove_voter(voter_id)
        option = session.query(PollOptionDB).get(poll_option_id)
        if option:
            if option not in self.options:
                raise ValueError("Poll option does not belong to this poll.")
            option.add_voter(voter_id)
            session.commit()

    def has_voted(self, voter_id: str) -> bool:
        for option in self.options:
            if str(voter_id) in option.voters_ids:
                return True
        return False

    def update_message_url(self, message_url: str) -> None:
        self.message_url = message_url
        session.commit()

    def update_end(self, end: datetime) -> None:
        self.end = end
        session.commit()

    def update_closed(self, closed: bool, author_id: str, time: datetime) -> None:
        self.closed = closed
        self.closed_by = str(author_id)
        self.closed_datetime = time
        session.commit()

    def remove(self) -> None:
        session.delete(self)
        session.commit()

    def get_voters_count(self) -> int:
        voters_count = 0
        for option in self.options:
            voters_count += option.voters_count
        return voters_count

    def get_voters(self) -> dict[PollOptionDB, set[str]]:
        voters_ids = {}
        for option in self.options:
            voters_ids[option] = option.voters_ids
        return voters_ids

    def get_winning_options(self) -> list[PollOptionDB]:
        max_votes = max(option.voters_count for option in self.options)
        winning_options = [option for option in self.options if option.voters_count == max_votes]
        return winning_options


class PollOptionDB(database.base):
    __tablename__ = "poll_option"

    id = Column(Integer, primary_key=True)
    emoji = Column(String, nullable=True)
    text = Column(String, nullable=False)
    voters = relationship(VoterDB, back_populates="poll_option", cascade="all,delete", collection_class=set)
    poll: Mapped[PollDB] = relationship(back_populates="options")
    poll_id = mapped_column(ForeignKey("poll.id"), nullable=False)

    # unique text for options per poll
    __table_args__ = (
        UniqueConstraint("text", "poll_id"),
    )

    @property
    def voters_count(self) -> int:
        return len(self.voters)

    @hybrid_property
    def voters_ids(self) -> set[str]:
        return {voter.id for voter in self.voters}

    @classmethod
    def get(cls, poll_option_id: int) -> PollOptionDB | None:
        return session.query(cls).get(poll_option_id)

    @classmethod
    def add(cls, text: str, emoji: str, poll_id: int) -> None:
        vote = cls(text=text, emoji=emoji, poll_id=poll_id)
        session.add(vote)
        session.commit()

    def remove_voter(self, voter: VoterDB | str) -> None:
        if isinstance(voter, str):
            voter = VoterDB.get(voter, self.id)

        if voter:
            session.delete(voter)
            session.commit()

    def add_voter(self, voter_id: str):
        voter = VoterDB.get(voter_id, self.id)
        if not voter:
            voter = VoterDB.add(voter_id, self.id)
        self.voters.add(voter)
        session.commit()

    def add_voters(self, voters_ids: list[str]):
        voters = []
        for voter_id in voters_ids:
            voter = VoterDB.get(voter_id, self.id)
            if not voter:
                voter = VoterDB.add(voter_id, self.id)
            if voter not in self.voters:
                voter = VoterDB(id=str(voter_id), poll_option_id=self.id)
                voters.append(voter)
        session.add_all(voter)
        session.commit()
