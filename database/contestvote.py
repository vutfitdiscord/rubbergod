from __future__ import annotations

from typing import Optional

from sqlalchemy import BigInteger, Column, String

from database import database, session


class ContestVoteDB(database.base):
    __tablename__ = "contest_vote"

    user_id = Column(String, nullable=False)
    contribution_id = Column(BigInteger, primary_key=True, nullable=False, autoincrement=True)

    @property
    def has_contributions(self) -> int:
        count = session.query(ContestVoteDB).filter_by(user_id=self.user_id).count()
        return count

    @classmethod
    def add_contribution(cls, user_id: str) -> ContestVoteDB:
        user = cls(user_id=str(user_id))
        session.add(user)
        session.commit()
        return user.contribution_id

    @classmethod
    def delete_contribution(cls, contribution_id: int) -> None:
        session.query(cls).filter_by(contribution_id=contribution_id).delete()
        session.commit()

    @classmethod
    def get_user(cls, user_id: str) -> ContestVoteDB:
        return session.query(cls).filter_by(user_id=str(user_id)).first()

    @classmethod
    def get_contribution_author(cls, contribution_id: int) -> Optional[str]:
        contribution = session.query(cls).filter_by(contribution_id=contribution_id).first()
        if contribution:
            return contribution.user_id
        return
