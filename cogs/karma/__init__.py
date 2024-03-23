from disnake.ext.commands import Bot

from .cog import Karma


def setup(bot: Bot):
    bot.add_cog(Karma(bot))
