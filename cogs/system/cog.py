"""
Core cog for bot. Can't be unloaded. Contains commands for cog management.
"""

import subprocess
from datetime import datetime

import disnake
from disnake.ext import commands

import utils
from cogs.base import Base
from config import cooldowns
from database.error import ErrorLogDB
from features.error import ErrorLogger
from features.git import Git
from permissions import permission_check

from . import features
from .messages_cz import MessagesCZ
from .views import View

boottime = datetime.now().replace(microsecond=0)


class System(Base, commands.Cog):
    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot
        self.error_log = ErrorLogger(bot)
        self.git = Git()

        self.unloadable_cogs = ["system"]

    @commands.check(permission_check.is_bot_admin)
    @commands.slash_command(name="git")
    async def git(self, inter: disnake.ApplicationCommandInteraction):
        pass

    @git.sub_command(name="pull", description=MessagesCZ.git_pull_brief)
    async def pull(self, inter: disnake.ApplicationCommandInteraction):
        await inter.send("Pulling...")
        message: disnake.Message = await inter.original_message()

        pull_result = await self.git.pull()
        pull_parts = utils.cut_string(pull_result, 1900)

        await message.edit(content=f"```{pull_parts[0]}```")

        for part in pull_parts[1:]:
            await inter.send(f"```{part}```")

    @commands.check(permission_check.is_bot_admin)
    @commands.slash_command(name="get_logs", description=MessagesCZ.get_logs_brief)
    async def get_logs(
        self,
        inter: disnake.ApplicationCommandInteraction,
        lines: int = commands.Param(100, ge=0, description=MessagesCZ.lines_param),
    ):
        await inter.response.defer()
        try:
            result = subprocess.run(
                f"touch service_logs.txt && tail -n {lines} service_logs.txt",
                shell=True,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
        except subprocess.CalledProcessError as error:
            strings = utils.cut_string(error.stderr, 1900)
            for string in strings:
                await inter.send(f"```{string}```")
            return

        with open("service_logs.txt", "w") as file:
            file.write(result.stdout)

        await inter.send(file=disnake.File("service_logs.txt"))

    @commands.check(permission_check.is_bot_admin)
    @commands.slash_command(name="shutdown", description=MessagesCZ.shutdown_brief)
    async def shutdown(self, inter: disnake.ApplicationCommandInteraction):
        await inter.send("Shutting down...")
        exit(1)

    @commands.check(permission_check.is_bot_admin)
    @commands.slash_command(name="cogs", description=MessagesCZ.cogs_brief, guild_ids=[Base.config.guild_id])
    async def cogs(self, inter: disnake.ApplicationCommandInteraction):
        """
        Creates embed with button and select(s) to load/unload/reload cogs.

        Max number of cogs can be 100 (4x25).
        """
        await inter.response.defer()
        cogs = await features.split_cogs()
        view = View(self.bot, cogs)
        embed = features.create_embed(self.bot)
        message = await inter.followup.send(embed=embed, view=view)

        # pass message object to classes
        view.message = message
        for i in range(len(cogs)):
            view.selects[i].message = message

    @cooldowns.default_cooldown
    @commands.slash_command(name="uptime", description=MessagesCZ.uptime_brief)
    async def uptime(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer()
        now = datetime.now().replace(microsecond=0)
        delta = now - boottime
        count = self.error_log.log_error_time(set=False)
        embed = disnake.Embed(
            title="Uptime",
            description=f"{count} days without an accident.",
            color=0xEEE657,
        )
        start_streak, end_streak = ErrorLogDB.get_longest_streak()
        embed.add_field(name=MessagesCZ.upsince_title, value=str(boottime))
        embed.add_field(name=MessagesCZ.uptime_title, value=str(delta))
        embed.add_field(name=MessagesCZ.uptime_latency, value=f"{round(self.bot.latency * 1000)} ms")
        embed.add_field(
            name=MessagesCZ.longest_streak,
            value=f"**{(end_streak - start_streak).days} day(s)**\n{start_streak} — {end_streak}",
            inline=False,
        )
        self.error_log.set_image(embed, self.bot.user, count)
        await inter.edit_original_response(embed=embed)
