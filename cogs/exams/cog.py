"""
Cog to parse exams data from website and send it to channel.
Available for each year of study.
"""

import re

import disnake
from disnake.ext import commands, tasks

from cogs.base import Base
from database.exams import ExamsTermsMessageDB
from permissions.checks import PermissionsCheck
from rubbergod import Rubbergod
from utils import cooldowns

from .features import YEAR_LIST, Features, year_regex
from .messages_cz import MessagesCZ


class Exams(Base, commands.Cog):
    def __init__(self, bot: Rubbergod):
        super().__init__()
        self.bot = bot
        self.features = Features(bot)

        self.subscribed_guilds: list[int] = []
        if self.config.exams_subscribe_default_guild:
            self.subscribed_guilds.append(self.config.guild_id)

        if self.subscribed_guilds:
            self.tasks = [self.update_terms_task.start()]

    @commands.slash_command(name="exams", description=MessagesCZ.exams_brief)
    async def exams(
        self,
        inter: disnake.ApplicationCommandInteraction,
        rocnik: str = commands.Param(name="rocnik", choices=YEAR_LIST, default=None),
    ):
        await inter.response.defer()
        if rocnik is None:
            if isinstance(inter.author, disnake.Member):
                user_roles: list[disnake.Role] = inter.author.roles

                for role in user_roles:
                    match = re.match(year_regex, role.name.upper())

                    if match is not None:
                        rocnik = self.features.process_match(match)
                        if rocnik is not None:
                            await self.features.process_exams(inter, rocnik, inter.author)
                            return

                await inter.edit_original_response(MessagesCZ.no_valid_role)
            else:
                await inter.edit_original_response(MessagesCZ.specify_year)
        else:
            await self.features.process_exams(inter, rocnik, inter.author)

    @cooldowns.default_cooldown
    @PermissionsCheck.is_helper_plus()
    @commands.slash_command(name="terms")
    async def terms(self, inter: disnake.ApplicationCommandInteraction):
        """Group of commands for terms."""
        await inter.response.defer()

    @terms.sub_command(name="update", description=MessagesCZ.update_term_brief)
    async def update(self, inter: disnake.ApplicationCommandInteraction):
        updated_chans = await self.features.update_exam_terms(inter.guild, inter.author)
        await inter.edit_original_response(MessagesCZ.terms_updated(num_chan=updated_chans))

    @PermissionsCheck.is_mod_plus()
    @terms.sub_command(name="remove_all", description=MessagesCZ.remove_all_terms_brief)
    async def remove_all(self, inter: disnake.ApplicationCommandInteraction):
        for channel in inter.guild.channels:
            if not isinstance(channel, disnake.TextChannel):
                continue

            for channel_name in self.config.exams_term_channels:
                if channel_name.lower() == channel.name.lower():
                    message_ids = ExamsTermsMessageDB.remove_from_channel(channel.id)
                    for message_id in message_ids:
                        try:
                            message = await channel.fetch_message(message_id)
                            await message.delete()
                        except disnake.NotFound:
                            pass
        await inter.edit_original_response(MessagesCZ.terms_removed)

    @PermissionsCheck.is_mod_plus()
    @terms.sub_command(name="remove", description=MessagesCZ.remove_terms_brief)
    async def remove(self, inter: disnake.ApplicationCommandInteraction, channel: disnake.TextChannel):
        if not isinstance(channel, disnake.TextChannel):
            await inter.edit_original_response(MessagesCZ.channel_is_not_text_channel(chan_name=channel.name))
            return

        message_ids = ExamsTermsMessageDB.remove_from_channel(channel.id)
        for message_id in message_ids:
            try:
                message = await channel.fetch_message(message_id)
                await message.delete()
            except disnake.NotFound:
                pass

        if message_ids:
            await inter.send(MessagesCZ.terms_removed)
        else:
            await inter.send(MessagesCZ.nothing_to_remove(chan_name=channel.name))

    @PermissionsCheck.is_mod_plus()
    @terms.sub_command(name="start", description=MessagesCZ.start_terms_brief)
    async def start(self, inter: disnake.ApplicationCommandInteraction):
        if inter.guild.id not in self.subscribed_guilds:
            self.subscribed_guilds.append(inter.guild.id)

        if not self.update_terms_task.is_running():
            self.update_terms_task.start()
        else:
            # If task is already running update terms now
            await self.features.update_exam_terms(inter.guild)

        await inter.send(MessagesCZ.automatic_update_started(guild_name=inter.guild.name))

    @PermissionsCheck.is_mod_plus()
    @terms.sub_command(name="stop", description=MessagesCZ.stop_terms_brief)
    async def stop(self, inter: disnake.ApplicationCommandInteraction):
        if inter.guild in self.subscribed_guilds:
            self.subscribed_guilds.remove(inter.guild.id)

        # If there are no subscribed guilds terminate whole task
        if not self.subscribed_guilds:
            self.update_terms_task.cancel()

        await inter.send(MessagesCZ.automatic_update_stopped(guild_name=inter.guild.name))

    @tasks.loop(hours=int(Base.config.exams_terms_update_interval * 24))
    async def update_terms_task(self):
        for guild in self.subscribed_guilds:
            guild = disnake.utils.get(self.bot.guilds, id=guild)
            if guild is not None:
                await self.features.update_exam_terms(guild)
