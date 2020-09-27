from sqlalchemy import Column, Integer, BIGINT

from repository.database import database


class HugsTable(database.base):
    __tablename__ = "bot_hugs"

    member_id = Column(BIGINT, primary_key=True, nullable=False, unique=True, autoincrement=False)

    # indexes make ~3s difference on table with 2.5k rows,
    # when polling for 'oder by <received> [desc]' (leaderboards etc.)
    given = Column(Integer, default=0, nullable=False, index=True)
    received = Column(Integer, default=0, nullable=False, index=True)
