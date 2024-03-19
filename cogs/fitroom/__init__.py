from disnake.ext.commands import Bot

from .cog import FitRoom


def setup(bot: Bot):
    bot.add_cog(FitRoom(bot))
