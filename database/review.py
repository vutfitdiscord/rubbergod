from __future__ import annotations

import datetime
import math
from typing import List, Optional

from sqlalchemy import (Boolean, Column, Date, ForeignKey, Integer,
                        PrimaryKeyConstraint, String, asc, desc, func)
from sqlalchemy.engine import Row
from sqlalchemy.orm import Query, relationship

from database import database, session


class ReviewDB(database.base):
    __tablename__ = "bot_review"

    id = Column(Integer, primary_key=True)
    member_ID = Column(String)
    anonym = Column(Boolean, default=True)
    subject = Column(String, ForeignKey("bot_subjects.shortcut", ondelete="CASCADE"))
    tier = Column(Integer, default=0)
    text_review = Column(String, default=None)
    date = Column(Date)
    relevance = relationship("ReviewRelevanceDB")

    @classmethod
    def get_review_by_id(cls, id: int) -> Optional[ReviewDB]:
        return session.query(cls).filter(cls.id == id).one_or_none()

    @classmethod
    def get_subject_reviews(cls, subject: str) -> List[object]:
        # return object with 'ReviewDB' and 'total' properties
        return (
            session.query(
                cls,
                func.count(cls.relevance).filter(ReviewRelevanceDB.vote).label("total"),
            )
            .filter(cls.subject == subject)
            .outerjoin(cls.relevance)
            .group_by(cls)
            .order_by(desc("total"))
            .all()
        )

    @classmethod
    def get_review_by_author_subject(cls, author_id: int, subject: str) -> Optional[ReviewDB]:
        return (
            session.query(cls)
            .filter(cls.subject == subject, cls.member_ID == str(author_id))
            .first()
        )

    @classmethod
    def get_reviews_by_author(cls, author_id: str) -> Query:
        return (
            session.query(cls)
            .filter(cls.member_ID == str(author_id))
        )

    @classmethod
    def add_review(cls, author: str, subject: str, tier: int, anonym: bool, text: str) -> None:
        review = cls(
            member_ID=str(author),
            subject=subject,
            tier=tier,
            anonym=anonym,
            text_review=text,
            date=datetime.date.today(),
        )
        session.add(review)
        session.commit()

    def remove(self) -> None:
        session.delete(self)
        session.commit()

    def update(self) -> None:
        self.date = datetime.date.today()
        session.merge(self)
        session.commit()


class ReviewRelevanceDB(database.base):
    __tablename__ = "bot_review_relevance"
    __table_args__ = (PrimaryKeyConstraint("review", "member_ID", name="key"),)

    member_ID = Column(String)
    vote = Column(Boolean, default=False)
    review = Column(Integer, ForeignKey("bot_review.id", ondelete="CASCADE"))

    @classmethod
    def get_votes_count(cls, review_id: int, vote: bool) -> int:
        return (
            session.query(cls)
            .filter(cls.review == review_id, cls.vote == vote)
            .count()
        )

    @classmethod
    def get_vote_by_author(cls, review_id: int, author_id: str) -> Optional[ReviewRelevanceDB]:
        return (
            session.query(cls)
            .filter(cls.review == review_id, cls.member_ID == author_id)
            .first()
        )

    @classmethod
    def add_vote(cls, review_id: int, vote: bool, author_id: str) -> None:
        relevance = cls(member_ID=author_id, vote=vote, review=review_id)
        session.merge(relevance)
        session.commit()

    @classmethod
    def remove_vote(cls, review_id: int, author_id: str) -> None:
        session.query(cls).filter(cls.review == review_id, cls.member_ID == author_id).delete()


class SubjectDB(database.base):
    __tablename__ = "bot_subjects"

    shortcut = Column(String, primary_key=True)
    reviews = relationship("ReviewDB")

    @classmethod
    def get(cls, shortcut: str) -> Optional[SubjectDB]:
        return session.query(cls).filter(cls.shortcut == shortcut).first()

    @classmethod
    def get_all(cls) -> List[SubjectDB]:
        return session.query(cls.shortcut).all()

    @classmethod
    def add(cls, shortcut: str) -> None:
        subject = cls(shortcut=shortcut)
        session.merge(subject)
        session.commit()


class SubjectDetailsDB(database.base):
    __tablename__ = "bot_subjects_details"

    shortcut = Column(String, primary_key=True)
    name = Column(String)
    credits = Column(Integer)
    semester = Column(String)
    end = Column(String)
    card = Column(String)
    year = Column(String)
    type = Column(String)
    degree = Column(String)

    @classmethod
    def get(cls, shortcut: str) -> Optional[SubjectDetailsDB]:
        return (
            session.query(cls)
            .filter(cls.shortcut.ilike(shortcut))
            .one_or_none()
        )

    def update(self) -> None:
        session.merge(self)
        session.commit()

    @classmethod
    def gen_tierboard_subquery(cls, type: str, sem: str, degree: str, year: str) -> Query:
        return (
            session.query(SubjectDB.reviews, SubjectDetailsDB, func.avg(ReviewDB.tier).label("avg_tier"))
            .outerjoin(SubjectDB.reviews)
            .group_by(SubjectDB)
            .outerjoin(SubjectDetailsDB, SubjectDetailsDB.shortcut.ilike(SubjectDB.shortcut))
            .group_by(SubjectDetailsDB.shortcut)
            .group_by(ReviewDB.subject)
            .filter(SubjectDetailsDB.degree.contains(degree))
            .filter(SubjectDetailsDB.type.contains(type))
            .filter(SubjectDetailsDB.semester.contains(sem))
            .filter(SubjectDetailsDB.year.contains(year))
            .subquery()
        )

    @classmethod
    def get_tierboard(cls, type: str, sem: str, degree: str, year: str, offset: int = 0) -> List[Row]:
        subquery = cls.gen_tierboard_subquery(type, sem, degree, year)
        return (
            session.query(subquery.c.shortcut, subquery.c.avg_tier)
            .filter(subquery.c.avg_tier != None)  # noqa: E711
            .order_by(asc("avg_tier"))
            .offset(offset)
            .limit(10)
            .all()
        )

    @classmethod
    def get_tierboard_page_count(cls, type: str, sem: str, degree: str, year: str) -> int:
        subquery = cls.gen_tierboard_subquery(type, sem, degree, year)
        return math.ceil((
            session.query(subquery.c.shortcut, subquery.c.avg_tier)
            .filter(subquery.c.avg_tier != None)  # noqa: E711
            .order_by(asc("avg_tier"))
            .count()
        )/10)


class ProgrammeDB(database.base):
    __tablename__ = "bot_programme"

    shortcut = Column(String, primary_key=True)
    name = Column(String)
    link = Column(String)

    @classmethod
    def get(cls, shortcut: str) -> Optional[ProgrammeDB]:
        return session.query(cls).filter(cls.shortcut == shortcut).first()

    @classmethod
    def get_all(cls) -> List[ProgrammeDB]:
        return session.query(cls.shortcut).all()

    @classmethod
    def set(cls, shortcut: str, name: str, link: str) -> None:
        programme = cls(
            shortcut=shortcut,
            name=name,
            link=link
        )
        session.merge(programme)
        session.commit()
