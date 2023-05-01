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
from config.app_config import config
from config.messages import Messages
from features.error import ErrorLogger
from features.git import Git
from permissions import permission_check

boottime = datetime.now().replace(microsecond=0)


class System(Base, commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.error_log = ErrorLogger()
        self.git = Git()

        self.unloadable_cogs = ["system"]

    @commands.group(pass_context=True)
    async def git(self, ctx: commands.Context):
        pass

    @git.command(brief=Messages.git_pull_brief)
    @commands.check(permission_check.is_bot_admin)
    async def pull(self, ctx: commands.Context):
        message: Message = await ctx.send("Pulling")

        pull_result = await self.git.pull()
        pull_parts = utils.cut_string(pull_result, 1900)

        await message.edit(content=f"```{pull_parts[0]}```")

        for part in pull_parts[1:]:
            await ctx.send(f"```{part}```")

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
    @commands.slash_command(name="cogs", description=Messages.cogs_brief, guild_ids=[config.guild_id])
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
        now = datetime.now().replace(microsecond=0)
        delta = now - boottime
        count = self.error_log.log_error_date(set=False)
        embed = disnake.Embed(
            title="Uptime",
            description=f"{count} days without an accident.",
            color=0xeee657,
        )
        embed.add_field(name=Messages.upsince_title, value=str(boottime))
        embed.add_field(name=Messages.uptime_title, value=str(delta))
        self.error_log.set_image(embed, self.bot.user, count)
        await inter.send(embed=embed)

    @pull.error
    @cogs.error
    async def on_command_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.errors.CommandInvokeError):
            if isinstance(error.__cause__, commands.errors.ExtensionAlreadyLoaded):
                await ctx.send(utils.fill_message("cog_is_loaded", cog=error.__cause__.name))
                return True
            elif isinstance(error.__cause__, commands.errors.ExtensionNotLoaded):
                await ctx.send(utils.fill_message("cog_is_unloaded", cog=error.__cause__.name))
                return True


def setup(bot):
    bot.add_cog(System(bot))
