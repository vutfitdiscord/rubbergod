from __future__ import annotations

from sqlalchemy import BigInteger, Column, String

from database import database


class CooldownDB(database.base):
    __tablename__ = "cooldowns"

    command_name = Column(String, primary_key=True, nullable=False)
    user_id = Column(String, primary_key=True, nullable=False)
    timestamp = Column(BigInteger, nullable=False)
