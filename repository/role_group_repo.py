import utils
from sqlalchemy import func
from repository.base_repository import BaseRepository
from repository.database import session
from repository.database.role_group import RoleGroup


class RoleGroupRepository(BaseRepository):

    def __init__(self):
        super().__init__()

    def group_names(self):
        return [group.name for group in self.groups]

    def groups(self):
        return session.query(RoleGroup)

    def get_group(self, name):
        query = session.query(RoleGroup).filter(RoleGroup.name == name)
        return query.one_or_none()

    def add_group(self, name):
        group = RoleGroup(name=name)
        session.add(group)
        session.commit()

    def group_add_channel_id(self, name, channel_id)
        group = self.get_group(name)
        group.channel_ids.append(channel_id)
        session.commit()

    def group_add_role_id(self, name, role_id)
        group = self.get_group(name)
        group.role_ids.append(role_ids)
        session.commit()

    def group_reset_channels(self, name)
        group = self.get_group(name)
        group.channel_ids = []
        session.commit()

    def group_reset_roles(self, name)
        group = self.get_group(name)
        group.role_ids = []
        session.commit()
