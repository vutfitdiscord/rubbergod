from disnake.ext.commands import Bot

from .cog import Gif


def setup(bot: Bot):
    bot.add_cog(Gif(bot))
