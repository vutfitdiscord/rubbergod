"""
Cog implementing anonymous reporting from users.
"""

import disnake
from disnake.ext import commands

from buttons.general import TrashView
from cogs.base import Base
from database.report import UserDB
from permissions.checks import PermissionsCheck
from rubbergod import Rubbergod
from utils import cooldowns

from .messages_cz import MessagesCZ
from .modals import Modal
from .views import ReportAnonymView, ReportAnswerOnlyView, ReportGeneralView, ReportMessageView


class Report(Base, commands.Cog):
    def __init__(self, bot: Rubbergod):
        super().__init__()
        self.bot = bot

    @commands.Cog.listener("on_ready")
    async def init_views(self):
        """Instantiate views for persistent interactions with bot"""
        self.bot.add_view(ReportAnonymView(self.bot))
        self.bot.add_view(ReportAnswerOnlyView(self.bot))
        self.bot.add_view(ReportGeneralView(self.bot))
        self.bot.add_view(ReportMessageView(self.bot))

    async def check_blocked_bot(self, inter: disnake.Interaction) -> disnake.Message | None:
        try:
            dm_message = await inter.author.send(MessagesCZ.check_dm, view=TrashView())
            return dm_message
        except disnake.Forbidden:
            await inter.send(MessagesCZ.blocked_bot(user=inter.author.id), ephemeral=True)
            return None

    @cooldowns.default_cooldown
    @commands.message_command(name="Report message", guild_ids=[Base.config.guild_id])
    async def app_report_message(self, inter: disnake.MessageCommandInteraction, message: disnake.Message):
        if UserDB.is_banned(inter.author.id):
            await inter.send(MessagesCZ.user_banned, ephemeral=True)
            return
        dm_message = await self.check_blocked_bot(inter)
        if dm_message is None:
            return

        modal = Modal(self.bot, dm_message, "Message report", message)
        await inter.response.send_modal(modal=modal)

    @cooldowns.default_cooldown
    @commands.slash_command(
        name="report", description=MessagesCZ.report_brief, guild_ids=[Base.config.guild_id]
    )
    async def _report(self, inter: disnake.ApplicationCommandInteraction):
        if UserDB.is_banned(inter.author.id):
            await inter.send(MessagesCZ.user_banned, ephemeral=True)
            return

    @_report.sub_command(name="general", description=MessagesCZ.general_brief)
    async def report_general(self, inter: disnake.ApplicationCommandInteraction):
        dm_message = await self.check_blocked_bot(inter)
        if dm_message is None:
            return
        modal = Modal(self.bot, dm_message)
        await inter.response.send_modal(modal=modal)

    @_report.sub_command(name="message", description=MessagesCZ.message_brief)
    async def report_message(
        self,
        inter: disnake.ApplicationCommandInteraction,
        message: disnake.Message = commands.Param(description=MessagesCZ.message_param),
    ):
        dm_message = await self.check_blocked_bot(inter)
        if dm_message is None:
            return

        modal = Modal(self.bot, dm_message, "Message report", message)
        await inter.response.send_modal(modal=modal)

    @_report.sub_command(name="google_form", description=MessagesCZ.google_form_brief)
    async def report_google_form(self, inter: disnake.ApplicationCommandInteraction):
        await inter.send(MessagesCZ.google_form, ephemeral=True)

    @PermissionsCheck.is_submod_plus()
    @commands.slash_command(name="report_mod", description=MessagesCZ.report_brief)
    async def _report_mod(self, inter: disnake.ApplicationCommandInteraction): ...

    @_report_mod.sub_command(name="unban", description=MessagesCZ.unban_user_brief)
    async def report_unban_user(self, inter: disnake.ApplicationCommandInteraction, user: disnake.User):
        UserDB.unban_user(user.id)
        await inter.send(MessagesCZ.unban_user(user=user.mention))
