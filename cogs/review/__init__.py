from disnake.ext.commands import Bot

from .cog import Review


def setup(bot: Bot):
    bot.add_cog(Review(bot))
