"""
Core cog for bot. Can't be unloaded. Contains commands for cog management.
"""

import math
from datetime import datetime

import disnake
from disnake.ext import commands
from disnake.message import Message

import utils
from buttons.system import Dropdown, SystemView
from cogs.base import Base
from config import cooldowns
from config.messages import Messages
from database.error import ErrorLogDB
from features.error import ErrorLogger
from features.git import Git
from permissions import permission_check

boottime = datetime.now().replace(microsecond=0)


class System(Base, commands.Cog):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        self.error_log = ErrorLogger()
        self.git = Git()

        self.unloadable_cogs = ["system"]

    @commands.check(permission_check.is_bot_admin)
    @commands.slash_command(name="git")
    async def git(self, inter):
        pass

    @git.sub_command(name="pull", description=Messages.git_pull_brief)
    async def pull(self, inter: disnake.ApplicationCommandInteraction):
        await inter.send("Pulling...")
        message: Message = await inter.original_message()

        pull_result = await self.git.pull()
        pull_parts = utils.cut_string(pull_result, 1900)

        await message.edit(content=f"```{pull_parts[0]}```")

        for part in pull_parts[1:]:
            await inter.send(f"```{part}```")

    @commands.check(permission_check.is_bot_admin)
    @commands.slash_command(name="shutdown", description=Messages.shutdown_brief)
    async def shutdown(self, inter: disnake.ApplicationCommandInteraction):
        await inter.send("Shutting down...")
        await self.bot.close()
        exit(0)

    async def create_selects(self):
        """Slices dictionary of all cogs to chunks for select."""
        cog_files = list(utils.get_all_cogs().keys())
        cog_names = list(utils.get_all_cogs().values())
        all_selects = []

        # 25 is max number of options for one select
        chunks = math.ceil(len(cog_files)/25)
        cog_files = list(utils.split(cog_files, chunks))
        cog_names = list(utils.split(cog_names, chunks))
        for i in range(0, chunks):
            all_selects.append([cog_files[i], cog_names[i]])

        return all_selects

    @commands.check(permission_check.is_bot_admin)
    @commands.slash_command(name="cogs", description=Messages.cogs_brief, guild_ids=[Base.config.guild_id])
    async def cogs(self, inter: disnake.ApplicationCommandInteraction):
        """
        Creates embed with button and select(s) to load/unload/reload cogs.

        Max number of cogs can be 100 (4x25).
        """

        selects = await self.create_selects()
        view = SystemView(self.bot, len(selects), selects)
        embed = Dropdown.create_embed(self, inter.author.color)
        await inter.send(embed=embed, view=view)

        # pass message object to classes
        message = await inter.original_message()
        view.message = message
        for i, cogs in enumerate(selects):
            view.selects[i].msg = message

    @cooldowns.default_cooldown
    @commands.slash_command(name="uptime", description=Messages.uptime_brief)
    async def uptime(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer()
        now = datetime.now().replace(microsecond=0)
        delta = now - boottime
        count = self.error_log.log_error_date(set=False)
        embed = disnake.Embed(
            title="Uptime",
            description=f"{count} days without an accident.",
            color=0xeee657,
        )
        start_streak, end_streak = ErrorLogDB.get_longest_streak()
        embed.add_field(name=Messages.upsince_title, value=str(boottime))
        embed.add_field(name=Messages.uptime_title, value=str(delta))
        embed.add_field(name=Messages.uptime_latency, value=f"{round (self.bot.latency * 1000)} ms")
        embed.add_field(
            name=Messages.longest_streak,
            value=f"**{(end_streak - start_streak).days} day(s)**\n{start_streak} — {end_streak}",
            inline=False
        )
        self.error_log.set_image(embed, self.bot.user, count)
        await inter.edit_original_response(embed=embed)

    @pull.error
    @cogs.error
    async def on_command_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.errors.CommandInvokeError):
            if isinstance(error.__cause__, commands.errors.ExtensionAlreadyLoaded):
                await ctx.send(Messages.cog_is_loaded(cog=error.__cause__.name))
                return True
            elif isinstance(error.__cause__, commands.errors.ExtensionNotLoaded):
                await ctx.send(Messages.cog_is_unloaded(cog=error.__cause__.name))
                return True


def setup(bot):
    bot.add_cog(System(bot))
