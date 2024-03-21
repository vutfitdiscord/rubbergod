from disnake.ext.commands import Bot

from .cog import Meme


def setup(bot: Bot):
    bot.add_cog(Meme(bot))
