"""
Cog implementing anonymous reporting from users.
"""

from typing import Optional

import disnake
from disnake.ext import commands

from buttons.general import TrashView
from cogs.base import Base
from config import cooldowns
from config.messages import Messages
from database.report import UserDB
from modals.report import ReportModal
from permissions import permission_check


class Report(Base, commands.Cog):
    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot

    async def check_blocked_bot(self, inter: disnake.Interaction) -> Optional[disnake.Message]:
        try:
            dm_message = await inter.author.send(Messages.report_check_dm, view=TrashView())
            return dm_message
        except disnake.Forbidden:
            await inter.send(Messages.blocked_bot(user=inter.author.id), ephemeral=True)
            return

    @cooldowns.default_cooldown
    @commands.message_command(name="Report message", guild_ids=[Base.config.guild_id])
    async def app_report_message(self, inter: disnake.MessageCommandInteraction, message: disnake.Message):
        if UserDB.is_banned(inter.author.id):
            await inter.send(Messages.report_banned, ephemeral=True)
            return
        dm_message = await self.check_blocked_bot(inter)
        if dm_message is None:
            return

        modal = ReportModal(self.bot, dm_message, "Message report", message)
        await inter.response.send_modal(modal=modal)

    @cooldowns.default_cooldown
    @commands.slash_command(
        name="report", description=Messages.report_brief, guild_ids=[Base.config.guild_id]
    )
    async def _report(self, inter: disnake.ApplicationCommandInteraction):
        if UserDB.is_banned(inter.author.id):
            await inter.send(Messages.report_banned, ephemeral=True)
            return

    @_report.sub_command(name="general", description=Messages.report_general_brief)
    async def report_general(self, inter: disnake.ApplicationCommandInteraction):
        dm_message = await self.check_blocked_bot(inter)
        if dm_message is None:
            return
        modal = ReportModal(self.bot, dm_message)
        await inter.response.send_modal(modal=modal)

    @_report.sub_command(name="message", description=Messages.report_message_brief)
    async def report_message(
        self,
        inter: disnake.ApplicationCommandInteraction,
        message: str = commands.Param(description=Messages.report_message_param)
    ):
        try:
            message: disnake.Message = await commands.MessageConverter().convert(inter, message)
        except commands.MessageNotFound:
            await inter.send(Messages.report_message_not_found, ephemeral=True)
            return
        dm_message = await self.check_blocked_bot(inter)
        if dm_message is None:
            return

        modal = ReportModal(self.bot, dm_message, "Message report", message)
        await inter.response.send_modal(modal=modal)

    @_report.sub_command(name="google_form", description=Messages.report_google_form_brief)
    async def report_google_form(self, inter: disnake.ApplicationCommandInteraction):
        await inter.send(Messages.report_google_form, ephemeral=True)

    @commands.check(permission_check.submod_plus)
    @commands.slash_command(name="report_mod", description=Messages.report_brief)
    async def _report_mod(self, inter: disnake.ApplicationCommandInteraction): ...

    @_report_mod.sub_command(name="unban", description=Messages.report_unban_user_brief)
    async def report_unban_user(self, inter: disnake.ApplicationCommandInteraction, user: disnake.User):
        UserDB.unban_user(user.id)
        await inter.send(Messages.report_unban_user(user=user.mention))


def setup(bot):
    bot.add_cog(Report(bot))
