from sqlalchemy import BigInteger, Boolean, Column, DateTime, Interval, String

from repository.database import database


class Timeout(database.base):
    __tablename__ = "timeout"

    user_id = Column(BigInteger, primary_key=True)
    mod_id = Column(BigInteger)
    start = Column(DateTime)
    end = Column(DateTime)
    length = Column(Interval)
    reason = Column(String)
    isself = Column(Boolean)
