import datetime

from disnake.ext import commands

import utils
from config import cooldowns
from config.messages import Messages


boottime = datetime.datetime.now().replace(microsecond=0)


class Base(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @cooldowns.default_cooldown
    @commands.command(brief=Messages.uptime_brief)
    async def uptime(self, ctx):
        now = datetime.datetime.now().replace(microsecond=0)
        delta = now - boottime
        await ctx.send(utils.fill_message("uptime_message", boottime=str(boottime), uptime=str(delta)))


def setup(bot):
    bot.add_cog(Base(bot))
