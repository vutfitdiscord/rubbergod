from disnake.ext.commands import Bot

from .cog import Bookmark


def setup(bot: Bot):
    bot.add_cog(Bookmark(bot))
