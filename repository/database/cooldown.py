from __future__ import annotations

from sqlalchemy import Column, String, Integer

from repository.database import database


class Cooldown(database.base):
    __tablename__ = "cooldowns"

    command_name = Column(String, primary_key=True, nullable=False)
    user_id = Column(String, primary_key=True, nullable=False)
    timestamp = Column(Integer, nullable=False)
