from sqlalchemy import BigInteger, Column, DateTime, String
from repository.database import database


class Timeout(database.base):
    __tablename__ = "timeout"

    user_id = Column(BigInteger, primary_key=True)
    start = Column(DateTime)
    end = Column(DateTime)
    reason = Column(String)