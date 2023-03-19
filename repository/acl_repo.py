from repository.base_repository import BaseRepository
from repository.database import session
from repository.database.acl import (Acl_groups, Acl_role_binding, Acl_rules,
                                     Acl_user_binding)


class AclRepository(BaseRepository):

    def find_user_exception(self, member_id, target_id):
        user_exceptions = session.query(Acl_user_binding).\
            filter(Acl_user_binding.user_id == str(member_id)).all()

        for exception in user_exceptions:
            result = self.find_target_exception(exception.acl_group_id,
                                                target_id)
            if result is not None:
                return exception.perms

        return None

    def find_target_exception(self, acl_group_id, target_id):
        stack = [acl_group_id]
        while True:
            group_id = stack.pop()
            result = session.query(Acl_rules).\
                filter(Acl_rules.acl_snowflake == str(target_id),
                       Acl_rules.acl_group_id == group_id).one_or_none()

            if result is None:
                groups = session.query(Acl_groups).\
                    filter(Acl_groups.parent_id == group_id).all()
                for group in groups:
                    stack.append(group.id)
                if stack == []:
                    return None
            else:
                return result

    def get_role_perms(self, role, target_id):
        role_exceptions = session.query(Acl_role_binding).\
            filter(Acl_role_binding.role_id == str(role.id)).all()

        role_exceptions += session.query(Acl_role_binding).\
            filter(Acl_role_binding.role_id == None,  # noqa
                   Acl_role_binding.role_name == role.name).all()

        for exception in role_exceptions:
            result = self.find_target_exception(exception.acl_group_id,
                                                target_id)
            if result is not None:
                return exception.perms

        return None

    def add_group(self, name, parent_id=None):
        group = Acl_groups(name=name, parent_id=parent_id)
        session.add(group)
        session.commit()

    def edit_group(self, id, name, parent_id=None):
        group = Acl_groups(id=id, name=name, parent_id=parent_id)
        session.merge(group)
        session.commit()

    def del_group(self, id):
        session.query(Acl_groups).filter(Acl_groups.id == id).delete()
        # TODO delete children etcu

    def list_group(self, id=None):
        query = session.query(Acl_groups)
        if id is not None:
            query = query.filter(Acl_groups.id == id)
            # TODO add children

        return query.all()

    def add_rule(self, acl_group_id, acl_snowflake):
        # TODO check group id validity
        rule = Acl_rules(acl_group_id=acl_group_id,
                         acl_snowflake=acl_snowflake)
        session.add(rule)
        session.commit()

    def edit_rule(self, id, acl_group_id, acl_snowflake):
        rule = Acl_rules(id=id, acl_group_id=acl_group_id,
                         acl_snowflake=acl_snowflake)
        session.merge(rule)
        session.commit()

    def del_rule(self, id):
        session.query(Acl_rules).filter(Acl_rules.id == id).delete()

    def list_rule(self, id=None):
        query = session.query(Acl_rules)
        if id is not None:
            query = query.filter(Acl_rules.id == id)

        return query.all()

    def add_role(self, acl_group_id, role_id_name, perms):
        # TODO check group id validity
        try:
            int(role_id_name)
            role_id = role_id_name
            role_name = None
        except ValueError:
            role_id = None
            role_name = role_id_name

        rule = Acl_role_binding(acl_group_id=acl_group_id,
                                role_id=role_id, role_name=role_name,
                                perms=perms)
        session.add(rule)
        session.commit()

    def edit_role(self, id, acl_group_id, role_id_name, perms):
        try:
            int(role_id_name)
            role_id = role_id_name
            role_name = None
        except ValueError:
            role_id = None
            role_name = role_id_name
        rule = Acl_role_binding(id=id, acl_group_id=acl_group_id,
                                role_id=role_id, role_name=role_name,
                                perms=perms)
        session.merge(rule)
        session.commit()

    def del_role(self, id):
        session.query(Acl_role_binding).\
                filter(Acl_role_binding.id == id).delete()

    def list_role(self, id=None):
        query = session.query(Acl_role_binding)
        if id is not None:
            query = query.filter(Acl_role_binding.id == id)

        return query.all()

    def add_user(self, acl_group_id, user_id, perms):
        # TODO check group id validity
        rule = Acl_user_binding(acl_group_id=acl_group_id,
                                user_id=user_id, perms=perms)
        session.add(rule)
        session.commit()

    def edit_user(self, id, acl_group_id, user_id, perms):
        rule = Acl_role_binding(id=id, acl_group_id=acl_group_id,
                                user_id=user_id, perms=perms)
        session.merge(rule)
        session.commit()

    def del_user(self, id):
        session.query(Acl_user_binding).\
                filter(Acl_user_binding.id == id).delete()

    def list_user(self, id=None):
        query = session.query(Acl_user_binding)
        if id is not None:
            query = query.filter(Acl_user_binding.id == id)

        return query.all()
