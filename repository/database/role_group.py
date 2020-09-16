from sqlalchemy import Column, String
from sqlalchemy.types import PickleType
from sqlalchemy.ext.mutable import MutableList
from repository.database import database


class RoleGroup(database.base):
    __tablename__ = 'bot_role_group'

    name = Column(String, primary_key=True)
    role_ids = Column(MutableList.as_mutable(PickleType))
    channel_ids = Column(MutableList.as_mutable(PickleType))
