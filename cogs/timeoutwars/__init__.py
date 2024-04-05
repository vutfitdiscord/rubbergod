from disnake.ext.commands import Bot

from .cog import TimeoutWars


def setup(bot: Bot):
    bot.add_cog(TimeoutWars(bot))
