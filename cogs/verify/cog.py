"""
Cog for verification system. Enables users to verify themselves with xlogin00 and gain access to server.
"""

from io import BytesIO

import disnake
from disnake.ext import commands

from cogs.base import Base
from database.verification import DynamicVerifyDB
from features import verification
from features.table_generator import TableGenerator
from rubbergod import Rubbergod
from utils import cooldowns
from utils.checks import PermissionsCheck

from .features_dynamic_verify import DynamicVerifyManager
from .messages_cz import MessagesCZ
from .modals_dynamic_verify import DynamicVerifyEditModal


async def dynamic_verify_rules_autocomplete(inter: disnake.ApplicationCommandInteraction, user_input: str):
    service = DynamicVerifyManager(inter.bot)
    return service.get_rules_list()


class Verify(Base, commands.Cog):
    def __init__(self, bot: Rubbergod):
        super().__init__()
        self.bot = bot
        self.verification = verification.Verification(bot)
        self.dynamic_verify_manager = DynamicVerifyManager(bot)

    def is_valid_guild(ctx: disnake.ApplicationCommandInteraction) -> bool:
        return ctx.guild_id is None or ctx.guild_id == Base.config.guild_id

    @cooldowns.default_cooldown
    @commands.check(is_valid_guild)
    @commands.slash_command(name="verify", description=MessagesCZ.verify_brief, dm_permission=True)
    async def verify(
        self,
        inter: disnake.ApplicationCommandInteraction,
    ):
        await inter.response.defer(ephemeral=True)

    @verify.sub_command(name="vut", description=MessagesCZ.verify_brief)
    async def verify_vut(
        self,
        inter: disnake.ApplicationCommandInteraction,
        login: str = commands.Param(description=MessagesCZ.verify_login_parameter),
    ):
        login = login.lower()
        if await self.dynamic_verify_manager.can_apply_rule(inter.user, login):
            await self.dynamic_verify_manager.request_access(login, inter)
            return
        if await self.verification.send_code(login, inter, muni=False):
            await self.verification.clear_host_roles(inter)

    @verify.sub_command(name="muni", description=MessagesCZ.verify_brief)
    async def verify_muni(
        self,
        inter: disnake.ApplicationCommandInteraction,
        login: str = commands.Param(description=MessagesCZ.verify_login_parameter_muni),
    ):
        login = login.lower()
        if await self.dynamic_verify_manager.can_apply_rule(inter.user, login):
            await self.dynamic_verify_manager.request_access(login, inter)
            return
        if await self.verification.send_code(login, inter, muni=True):
            await self.verification.clear_host_roles(inter)

    @verify.error
    async def on_verification_error(self, inter: disnake.ApplicationCommandInteraction, error):
        if isinstance(error, commands.CheckFailure):
            await inter.send(MessagesCZ.verify_invalid_channel, ephemeral=True)
            return True

    @PermissionsCheck.is_in_modroom()
    @commands.slash_command(name="dynamic_verify", guild_ids=[Base.config.guild_id])
    async def dynamic_verify(self, inter: disnake.ApplicationCommandInteraction):
        """This method is only group for another commands. This function does nothing."""
        pass

    @dynamic_verify.sub_command(name="create", description=MessagesCZ.dynamic_verify_create_brief)
    async def dynamic_verify_create(self, inter: disnake.ApplicationCommandInteraction):
        modal = DynamicVerifyEditModal(inter.guild, None)
        await inter.response.send_modal(modal)

    @dynamic_verify.sub_command(name="list", description=MessagesCZ.dynamic_verify_list_brief)
    async def dynamic_verify_list(self, inter: disnake.ApplicationCommandInteraction):
        matrix = []
        for rule in DynamicVerifyDB.get_rules():
            roles = [inter.guild.get_role(role_id).name for role_id in rule.get_role_ids()]
            matrix.append([rule.id, rule.name, str(rule.enabled), str(rule.mod_check), ", ".join(roles)])
        generator = TableGenerator(header=["ID", "Name", "Enabled", "Mod check", "Roles"])
        generator.align(["c", "l", "c", "c", "l"])
        table = generator.generate_table(matrix)
        with BytesIO(bytes(table, "utf-8")) as file:
            file = disnake.File(fp=file, filename="dynamic_verify_list.txt")
        await inter.response.send_message(file=file)

    @dynamic_verify.sub_command(name="edit", description=MessagesCZ.dynamic_verify_edit_brief)
    async def dynamic_verify_edit(
        self,
        inter: disnake.ApplicationCommandInteraction,
        rule_id: str = commands.Param(
            autocomplete=dynamic_verify_rules_autocomplete, description=MessagesCZ.dynamic_verify_rule_id
        ),
    ):
        rule = self.dynamic_verify_manager.get_rule(rule_id)
        if rule is None:
            await inter.response.send_message(MessagesCZ.dynamic_verify_missing_rule(rule_id=rule_id))
            return
        modal = DynamicVerifyEditModal(inter.guild, rule)
        await inter.response.send_modal(modal)

    @dynamic_verify.sub_command(name="remove", description=MessagesCZ.dynamic_verify_remove_brief)
    async def dynamic_verify_remove(
        self,
        inter: disnake.ApplicationCommandInteraction,
        rule_id: str = commands.Param(
            autocomplete=dynamic_verify_rules_autocomplete, description=MessagesCZ.dynamic_verify_rule_id
        ),
    ):
        rule = self.dynamic_verify_manager.get_rule(rule_id)
        if rule is None:
            await inter.response.send_message(MessagesCZ.dynamic_verify_missing_rule(rule_id=rule_id))
            return
        rule.remove_rule()
        await inter.response.send_message(MessagesCZ.dynamic_verify_remove_success)

    @PermissionsCheck.is_submod_plus()
    @commands.user_command(name="Verify host", guild_ids=[Base.config.guild_id])
    async def verify_host(self, inter: disnake.UserCommandInteraction, member: disnake.Member):
        """add verify and host role to new member"""
        await inter.response.defer()
        host_id = inter.guild.get_role(self.config.verification_host_id)
        verify_id = inter.guild.get_role(self.config.verification_role_id)
        newbie_id = inter.guild.get_role(self.config.newbie_role)

        # check if user is still on server
        try:
            await member.remove_roles(newbie_id)
            await member.add_roles(host_id, verify_id)
        except AttributeError:
            raise commands.errors.MemberNotFound("Member not found")
        response_message = MessagesCZ.verify_verify_success(user=member.id)
        await inter.edit_original_response(response_message)

        try:
            await member.send(response_message)
        except disnake.Forbidden:
            await inter.send(MessagesCZ.blocked_bot(user=member.id))
