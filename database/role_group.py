from __future__ import annotations

from typing import List

from sqlalchemy import Column, String
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.types import PickleType

from database import database, session


class RoleGroupDB(database.base):
    __tablename__ = 'bot_role_group'

    name = Column(String, primary_key=True)
    role_ids = Column(MutableList.as_mutable(PickleType))
    channel_ids = Column(MutableList.as_mutable(PickleType))

    @classmethod
    def group_names(cls):
        return [group.name for group in cls.groups()]

    @classmethod
    def groups(cls) -> List[RoleGroupDB]:
        return session.query(cls).all()

    @classmethod
    def get_group(cls, name: str) -> RoleGroupDB:
        query = session.query(cls).filter(cls.name == str(name))
        return query.one_or_none()

    @classmethod
    def add_group(cls, name: str) -> None:
        group = cls(name=name, role_ids=[], channel_ids=[])
        session.add(group)
        session.commit()

    @classmethod
    def group_add_channel_id(cls, name: str, channel_id: str) -> None:
        group = cls.get_group(name)
        if group is not None:
            group.channel_ids.append(str(channel_id))
            session.commit()

    @classmethod
    def group_add_role_id(cls, name: str, role_id: str) -> None:
        group = cls.get_group(name)
        if group is not None:
            group.role_ids.append(str(role_id))
            session.commit()

    @classmethod
    def group_reset_channels(cls, name: str) -> None:
        group = cls.get_group(name)
        if group is not None:
            group.channel_ids = []
            session.commit()

    @classmethod
    def group_reset_roles(cls, name: str) -> None:
        group = cls.get_group(name)
        if group is not None:
            group.role_ids = []
            session.commit()

    @classmethod
    def group_delete(cls, name: str) -> None:
        session.query(cls).filter(cls.name == str(name)).delete()
