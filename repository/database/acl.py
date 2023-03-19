from sqlalchemy import Column, ForeignKey, Integer, String

from repository.database import database


class Acl_groups(database.base):
    __tablename__ = 'bot_acl_groups'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    parent_id = Column(Integer)


class Acl_rules(database.base):
    __tablename__ = 'bot_acl_rules'

    id = Column(Integer, primary_key=True)
    acl_group_id = Column(Integer, ForeignKey('bot_acl_groups.id',
                                              ondelete='CASCADE'))
    acl_snowflake = Column(String)


class Acl_role_binding(database.base):
    __tablename__ = 'bot_acl_roles'

    id = Column(Integer, primary_key=True)
    acl_group_id = Column(Integer, ForeignKey('bot_acl_groups.id',
                                              ondelete='CASCADE'))
    role_id = Column(String, default=None)
    role_name = Column(String)
    perms = Column(Integer)


class Acl_user_binding(database.base):
    __tablename__ = 'bot_acl_users'

    id = Column(Integer, primary_key=True)
    acl_group_id = Column(Integer, ForeignKey('bot_acl_groups.id',
                                              ondelete='CASCADE'))
    user_id = Column(String)
    perms = Column(Integer)
