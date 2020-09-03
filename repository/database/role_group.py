from sqlalchemy import Column, String, Integer
from sqlalchemy.types import ARRAY
from repository.database import database


class RoleGroup(database.base):
    __tablename__ = 'bot_role_group'

    name = Column(String, primary_key=True)
    role_ids = Column(ARRAY(Integer))
    channel_ids = Column(ARRAY(Integer))
