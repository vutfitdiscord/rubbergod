import disnake
from disnake.ext import commands

import utils
from config import cooldowns
from config.app_config import config
from config.messages import Messages
from features import verification
from features.dynamic_verify import DynamicVerifyManager
from modals.dynamic_verify import DynamicVerifyEditModal
from permissions import permission_check, room_check


async def dynamic_verify_rules_autocomplete(inter: disnake.ApplicationCommandInteraction, user_input: str):
    service = DynamicVerifyManager(inter.bot)
    return service.get_rules_list()


class Verify(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.verification = verification.Verification(bot)
        self.dynamic_verify_manager = DynamicVerifyManager(bot)

    def is_valid_guild(ctx: disnake.ApplicationCommandInteraction) -> bool:
        return ctx.guild_id is None or ctx.guild_id == config.guild_id

    @cooldowns.default_cooldown
    @commands.check(is_valid_guild)
    @commands.slash_command(name="verify", description=Messages.verify_brief, dm_permission=True)
    async def verify(
        self,
        inter: disnake.ApplicationCommandInteraction,
        login: str = commands.Param(description=Messages.verify_login_parameter),
    ):
        await inter.response.defer(ephemeral=True)
        if await self.dynamic_verify_manager.can_apply_rule(inter.user, login):
            await self.dynamic_verify_manager.request_access(login, inter)
            return
        await self.verification.clear_host_roles(inter)
        await self.verification.send_code(login, inter)

    @verify.error
    async def on_verification_error(self, inter: disnake.ApplicationCommandInteraction, error):
        if isinstance(error, commands.CheckFailure):
            await inter.send(Messages.verify_invalid_channel, ephemeral=True)
            return True

    @commands.check(room_check.is_in_modroom)
    @commands.slash_command(name="dynamic_verify", guild_ids=[config.guild_id])
    async def dynamic_verify(self, inter: disnake.ApplicationCommandInteraction):
        """This method is only group for another commands. This function does nothing."""
        pass

    @dynamic_verify.sub_command(name="create", description=Messages.dynamic_verify_create)
    async def dynamic_verify_create(self, inter: disnake.ApplicationCommandInteraction):
        modal = DynamicVerifyEditModal(inter.guild, None)
        await inter.response.send_modal(modal)

    @dynamic_verify.sub_command(name="edit", description=Messages.dynamic_verify_edit)
    async def dynamic_verify_edit(
        self,
        inter: disnake.ApplicationCommandInteraction,
        rule_id: str = commands.Param(
            autocomplete=dynamic_verify_rules_autocomplete, description=Messages.dynamic_verify_edit_rule_id
        ),
    ):
        rule = self.dynamic_verify_manager.get_rule(rule_id)
        if rule is None:
            await inter.response.send_message(
                utils.fill_message("dynamic_verify_missing_rule", rule_id=rule_id)
            )
            return
        modal = DynamicVerifyEditModal(inter.guild, rule)
        await inter.response.send_modal(modal)

    @commands.check(permission_check.submod_plus)
    @commands.user_command(name="Verify host", guild_ids=[config.guild_id])
    async def verify_host(self, inter: disnake.UserCommandInteraction, member: disnake.Member):
        """add verify and host role to new member"""
        host_id = inter.guild.get_role(config.verification_host_id)
        verify_id = inter.guild.get_role(config.verification_role_id)

        # check if user is still on server
        try:
            await member.add_roles(host_id, verify_id)
        except AttributeError:
            raise commands.errors.MemberNotFound("Member not found")
        await inter.response.send_message(Messages.verify_verify_success.format(user=member.mention))


def setup(bot):
    bot.add_cog(Verify(bot))
