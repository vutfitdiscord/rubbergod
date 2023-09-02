from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import database, session


class ReportDB(database.base):
    __tablename__ = "report"

    id = Column(Integer, primary_key=True, nullable=False, unique=True, autoincrement=True)
    type = Column(String, default="general", nullable=False)
    datetime = Column(DateTime, default=datetime.now(), nullable=False)
    author: Mapped[UserDB] = relationship(back_populates="reports")
    author_id: Mapped[String] = mapped_column(ForeignKey("report_user.id"))
    target_user_id = Column(String, default="", nullable=False)
    moderator_id = Column(String, default="", nullable=False)
    message_url = Column(String, default="", nullable=False)
    report_url = Column(String, default="", nullable=False)
    reason = Column(String, nullable=False)
    answers: Mapped[List[AnswerDB]] = relationship(back_populates="report")
    resolved = Column(Boolean, default=False, nullable=False)
    fake_report = Column(Boolean, default=False, nullable=False)

    @property
    def last_answer(self) -> str:
        """Returns the last answer of the report or the reason if there are no answers"""
        try:
            return self.answers[-1].content
        except IndexError:
            return self.reason

    @classmethod
    def is_resolved(cls, report_id: int) -> bool:
        report = cls.get_report(report_id)
        return report.resolved

    @classmethod
    def get_report(cls, report_id: int) -> Optional[ReportDB]:
        return session.query(cls).filter_by(id=int(report_id)).first()

    @classmethod
    def get_report_author(cls, report_id: int) -> Optional[UserDB]:
        report = cls.get_report(report_id)
        return report.author_id

    @classmethod
    def add_report(
        cls,
        type: str,
        author_id: str,
        reason: str,
        message_url: str = None,
        target_user_id: str = None
    ) -> int:
        report = ReportDB(
            type=type,
            author_id=str(author_id),
            reason=reason,
            message_url=message_url,
            target_user_id=str(target_user_id)
        )
        session.add(report)
        session.commit()
        return report.id

    @classmethod
    def set_resolved(cls, report_id: int, moderator_id: str, resolved: bool) -> None:
        """
        Report can be resolved by report author or moderator
        if report is solved by user, moderator_id is empty string
        """
        report = cls.get_report(int(report_id))
        if report is None:
            return

        report.resolved = resolved
        report.moderator_id = str(moderator_id)
        session.commit()

    @classmethod
    def set_fake_report(cls, report_id: int, moderator_id: str, fake_report: bool) -> None:
        """Report is fake, no other action needed"""
        report = cls.get_report(int(report_id))
        UserDB.ban_user(report.author_id)
        if report is None:
            return

        report.resolved = fake_report
        report.fake_report = fake_report
        report.moderator_id = str(moderator_id)
        session.commit()

    @classmethod
    def set_report_url(cls, report_id: int, report_url: str) -> None:
        report = cls.get_report(report_id)
        if report is None:
            return

        report.report_url = report_url
        session.commit()

    @classmethod
    def set_answer(cls, report_id: int, moderator_id: str, answer: str) -> None:
        report = cls.get_report(int(report_id))
        if report is None:
            return

        report.answer = answer
        report.moderator_id = str(moderator_id)
        session.commit()


class UserDB(database.base):
    __tablename__ = "report_user"

    id = Column(String, primary_key=True, nullable=False, unique=True)
    reports: Mapped[List[ReportDB]] = relationship(back_populates="author")
    banned = Column(Boolean, default=False, nullable=False)

    @classmethod
    def get_user(cls, user_id: str) -> Optional[UserDB]:
        return session.query(cls).filter_by(id=str(user_id)).first()

    @classmethod
    def get_fake_reports(cls, user_id: str) -> Optional[List[ReportDB]]:
        return session.query(ReportDB).filter_by(author_id=str(user_id), fake_report=True)

    @classmethod
    def is_banned(cls, user_id: str) -> bool:
        """Check if user is banned if user not found return None"""
        user = cls.get_user(str(user_id))
        if user is None:
            return False
        return user.banned

    @classmethod
    def add_user(cls, user_id: str) -> None:
        exists = cls.get_user(str(user_id))
        if exists is not None:
            return

        user = UserDB(id=str(user_id))
        session.add(user)
        session.commit()

    @classmethod
    def unban_user(cls, user_id: str) -> None:
        user = cls.get_user(str(user_id))
        if user is None:
            return

        user.banned = False
        session.commit()

    @classmethod
    def ban_user(cls, user_id: str) -> None:
        """Ban user if he has more than 3 false reports"""
        user = cls.get_user(str(user_id))
        fake_reports = session.query(ReportDB).filter_by(author_id=str(user_id), fake_report=True).count()
        if user is None:
            return

        if fake_reports < 3:
            return

        user.banned = True
        session.commit()


class AnswerDB(database.base):
    __tablename__ = "report_answer"

    id = Column(Integer, primary_key=True, nullable=False, unique=True)
    datetime = Column(DateTime, default=datetime.now(), nullable=False)
    report: Mapped[ReportDB] = relationship(back_populates="answers")
    report_id: Mapped[Integer] = mapped_column(ForeignKey("report.id"))
    author_id = Column(String, nullable=False)
    content = Column(String, default="", nullable=False)

    @classmethod
    def get_answer(cls, answer_id: int) -> Optional[AnswerDB]:
        return session.query(cls).filter_by(id=int(answer_id)).first()

    @classmethod
    def add_answer(cls, report_id: int, author_id: str, content: str) -> None:
        answer = AnswerDB(
            report_id=int(report_id),
            author_id=str(author_id),
            content=content
        )
        session.add(answer)
        session.commit()
