import utils
from utils import fill_message
from config import messages
from features.base_feature import BaseFeature
from repository.acl_repo import AclRepository

messages = messages.Messages


class Acl(BaseFeature):

    def __init__(self, acl_repository: AclRepository):
        self.acl_repo = acl_repository

    def get_perms(self, member_id, top_role, target, roles):
        if member_id is not None:
            perms = self.acl_repo.find_user_exception(member_id, target)
            if perms is not None:
                return perms

        perms = self.acl_repo.get_role_perms(top_role, target)

        return perms

    async def handle_add(self, ctx, args):
        if not len(args):
            await ctx.send(fill_message("acl_help", user=ctx.author.id))
            return

        if args[0] == "group" and 2 <= len(args) <= 3:
            await self.add_group(ctx, args[1:])
        elif args[0] == "rule" and len(args) == 3:
            await self.add_rule(ctx, args[1:])
        elif args[0] == "role" and len(args) == 4:
            await self.add_role(ctx, args[1:])
        elif args[0] == "user" and len(args) == 4:
            await self.add_user(ctx, args[1:])
        else:
            await ctx.send(fill_message("acl_help", user=ctx.author.id))
            return

    async def handle_edit(self, ctx, args):
        if not len(args):
            await ctx.send(fill_message("acl_help", user=ctx.author.id))
            return

        if args[0] == "group" and 3 <= len(args) <= 4:
            await self.edit_group(ctx, args[1:])
        elif args[0] == "rule" and len(args) == 3:
            await self.edit_rule(ctx, args[1:])
        elif args[0] == "role" and len(args) == 4:
            await self.edit_role(ctx, args[1:])
        elif args[0] == "user" and len(args) == 4:
            await self.edit_user(ctx, args[1:])
        else:
            await ctx.send(fill_message("acl_help", user=ctx.author.id))
            return

    async def handle_del(self, ctx, args):
        if not len(args):
            await ctx.send(fill_message("acl_help", user=ctx.author.id))
            return

        if args[0] == "group" and len(args) == 2:
            await self.del_group(ctx, args[1])
        elif args[0] == "rule" and len(args) == 2:
            await self.del_rule(ctx, args[1])
        elif args[0] == "role" and len(args) == 2:
            await self.del_role(ctx, args[1])
        elif args[0] == "user" and len(args) == 2:
            await self.del_user(ctx, args[1])
        else:
            await ctx.send(fill_message("acl_help", user=ctx.author.id))
            return

    async def handle_list(self, ctx, args):
        if not len(args) or len(args) > 2:
            await ctx.send(fill_message("acl_help", user=ctx.author.id))
            return

        if args[0] == "group":
            await self.list_group(ctx, args[1:])
        elif args[0] == "rule":
            await self.list_rule(ctx, args[1:])
        elif args[0] == "role":
            await self.list_role(ctx, args[1:])
        elif args[0] == "user":
            await self.list_user(ctx, args[1:])
        else:
            await ctx.send(fill_message("acl_help", user=ctx.author.id))
            return

    async def add_group(self, ctx, args):
        self.acl_repo.add_group(*args)
        await ctx.send(messages.acl_add_group)

    async def edit_group(self, ctx, args):
        self.acl_repo.edit_group(*args)
        await ctx.send(messages.acl_edit_group)

    async def del_group(self, ctx, id):
        self.acl_repo.del_group(id)
        await ctx.send(messages.acl_del_group)

    async def list_group(self, ctx, args):
        groups = self.acl_repo.list_group(*args)
        table = (("{:>20}" * 3) + '\n') * (len(groups) + 1)
        content = []
        for group in groups:
            content.append(str(group.id))
            content.append(str(group.name))
            content.append(str(group.parent_id))

        table = "```" + table.format("id", "name", "parent_id", *content) +\
                "```"
        await ctx.send(table)

    async def add_rule(self, ctx, args):
        self.acl_repo.add_rule(*args)
        await ctx.send(messages.acl_add_group)

    async def edit_rule(self, ctx, args):
        self.acl_repo.edit_rule(*args)
        await ctx.send(messages.acl_edit_rule)

    async def del_rule(self, ctx, id):
        self.acl_repo.del_rule(id)
        await ctx.send(messages.acl_del_rule)

    async def list_rule(self, ctx, args):
        rules = self.acl_repo.list_rule(*args)
        table = (("{:>20}" * 3) + '\n') * (len(rules) + 1)
        content = []
        for rule in rules:
            content.append(str(rule.id))
            content.append(str(rule.acl_group_id))
            content.append(str(rule.acl_snowflake))

        table = "```" + table.format("id", "acl_group_id", "acl_snowflake",
                                     *content) + "```"
        await ctx.send(table)

    async def add_role(self, ctx, args):
        self.acl_repo.add_role(*args)
        await ctx.send(messages.acl_add_role)

    async def edit_role(self, ctx, args):
        self.acl_repo.edit_role(*args)
        await ctx.send(messages.acl_edit_role)

    async def del_role(self, ctx, id):
        self.acl_repo.del_role(id)
        await ctx.send(messages.acl_del_role)

    async def list_role(self, ctx, args):
        roles = self.acl_repo.list_role(*args)
        table = (("{:>16}" * 5) + '\n') * (len(roles) + 1)
        content = []
        for role in roles:
            content.append(str(role.id))
            content.append(str(role.acl_group_id))
            content.append(str(role.role_id))
            content.append(str(role.role_name))
            content.append(str(role.perms))

        table = "```" + table.format("id", "acl_group_id", "role_id",
                                     "role_name", "perms", *content) +\
                "```"
        await ctx.send(table)

    async def add_user(self, ctx, args):
        self.acl_repo.add_user(*args)
        await ctx.send(messages.acl_add_user)

    async def edit_user(self, ctx, args):
        self.acl_repo.edit_user(*args)
        await ctx.send(messages.acl_edit_user)

    async def del_user(self, ctx, id):
        self.acl_repo.del_user(id)
        await ctx.send(messages.acl_del_user)

    async def list_user(self, ctx, args):
        users = self.acl_repo.list_user(*args)
        table = (("{:>18}" * 4) + '\n') * (len(users) + 1)
        content = []
        for user in users:
            content.append(str(user.id))
            content.append(str(user.acl_group_id))
            content.append(str(user.user_id))
            content.append(str(user.perms))

        table = "```" + table.format("id", "acl_group_id", "user_id", "perms",
                                     *content) + "```"
        await ctx.send(table)
