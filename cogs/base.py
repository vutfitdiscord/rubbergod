import datetime

from disnake.ext import commands
import disnake

from config import cooldowns
from config.messages import Messages
from features.error import ErrorLogger


boottime = datetime.datetime.now().replace(microsecond=0)


class Base(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.error_log = ErrorLogger()

    @cooldowns.default_cooldown
    @commands.command(brief=Messages.uptime_brief)
    async def uptime(self, ctx):
        now = datetime.datetime.now().replace(microsecond=0)
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
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Base(bot))
