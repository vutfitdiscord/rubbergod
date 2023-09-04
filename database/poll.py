from __future__ import annotations

from datetime import datetime
from enum import IntEnum
from typing import List, Optional

from sqlalchemy import (Boolean, Column, DateTime, ForeignKey, Integer, String,
                        UniqueConstraint)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.expression import or_

from database import database, session


class VoterDB(database.base):
    __tablename__ = "voter"

    id = Column(String, primary_key=True)
    poll_option_id = Column(Integer, ForeignKey("poll_option.id"))
    poll_option = relationship("PollOptionDB", back_populates="voters")

    @classmethod
    def add(cls, voter_id: str, poll_option_id: int) -> None:
        voter = cls(id=str(voter_id), poll_option_id=poll_option_id)
        session.add(voter)
        session.commit()
        return voter

    @classmethod
    def get(cls, voter_id: str) -> None:
        return session.query(cls).filter_by(id=str(voter_id)).first()


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
    end_datetime = Column(DateTime, nullable=True)
    options: Mapped[List[PollOptionDB]] = relationship(back_populates="poll")
    max_votes = Column(Integer, nullable=False)
    anonymous = Column(Boolean, nullable=False)

    @property
    def is_closed(self) -> bool:
        return self.end_datetime < datetime.now()

    @classmethod
    def add(
        cls,
        title: str,
        author_id: str,
        message_url: str,
        poll_type: PollType,
        end_datetime: datetime,
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
            end_datetime=end_datetime,
            anonymous=anonymous,
            max_votes=max_votes,
        )
        for emoji, option in poll_options.items():
            new_poll.options.append(PollOptionDB(emoji=emoji, text=option))
        session.add(new_poll)
        session.commit()
        return new_poll

    @classmethod
    def get(cls, poll_id: int) -> Optional[PollDB]:
        return session.query(cls).filter_by(id=poll_id).first()

    @classmethod
    def get_pending_polls(cls) -> Optional[List[PollDB]]:
        return session.query(cls).filter(or_(cls.end_datetime is None, cls.end_datetime >= datetime.now()))

    def remove_voter(self, voter: VoterDB) -> None:
        for option in self.options:
            option.remove_voter(voter)
        session.commit()

    def update_message_url(self, message_url: str) -> None:
        self.message_url = message_url
        session.commit()

    def remove(self) -> None:
        session.delete(self)
        session.commit()

    def get_voters_count(self) -> Optional[List[str]]:
        voters_count = 0
        for option in self.options:
            voters_count += option.voters_count
        return voters_count


class PollOptionDB(database.base):
    __tablename__ = "poll_option"

    id = Column(Integer, primary_key=True)
    emoji = Column(String, nullable=True)
    text = Column(String, nullable=False)
    voters = relationship(VoterDB, back_populates="poll_option", collection_class=set)
    poll: Mapped[PollDB] = relationship(back_populates="options")
    poll_id = mapped_column(ForeignKey("poll.id"), nullable=False)

    # unique text for options per poll
    __table_args__ = (
        UniqueConstraint("text", "poll_id"),
    )

    @property
    def voters_count(self) -> int:
        return len(self.voters)

    @property
    def voters_ids(self) -> List[str]:
        return [voter.id for voter in self.voters]

    @classmethod
    def add(cls, text: str, emoji: str, poll_id: int) -> None:
        vote = cls(text=text, emoji=emoji, poll_id=poll_id)
        session.add(vote)
        session.commit()

    def remove_voter(self, voter: VoterDB) -> None:
        if voter in self.voters:
            self.voters.remove(voter)
            session.commit()

    def add_voter(self, voter_id: str):
        voter = VoterDB.get(voter_id)
        if not voter:
            voter = VoterDB.add(voter_id, self.id)
        if voter not in self.voters:
            self.voters.add(voter)
        session.commit()

    def add_voters(self, voters_ids: List[str]):
        voters = []
        for voter_id in voters_ids:
            voter = VoterDB.get(voter_id)
            if not voter:
                voter = VoterDB.add(voter_id, self.id)
            if voter not in self.voters:
                voter = VoterDB(id=str(voter_id), poll_option_id=self.id)
                voters.append(voter)
        session.add_all(voter)
        session.commit()
