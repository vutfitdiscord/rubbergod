from disnake.ext.commands import Bot

from .cog import Timeout


def setup(bot: Bot):
    bot.add_cog(Timeout(bot))
