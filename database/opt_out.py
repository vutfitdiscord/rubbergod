from __future__ import annotations

from sqlalchemy import Column, String
from database import database, session

class OptOutDb(database.Base):
    __tablename__ = "opted_out"

    opted_out_id = Column(
        String,
        primary_key=True,
        nullable=False,
    )

    @classmethod
    def create(cls, opted_out_id: str) -> None:
        session.add(cls(opted_out_id=opted_out_id))
        session.commit()

    @classmethod
    def remove(cls, opted_out_id: str) -> None:
        opted_out = session.query(cls).filter(cls.opted_out_id == opted_out_id).first()

        if opted_out:
            session.delete(opted_out)
            session.commit()

    @classmethod
    def get_all(cls) -> list[str]:
        return [opted_out_id for opted_out_id in session.query(cls).all()]
