from disnake.ext.commands import Bot

from .cog import BetterMeme


def setup(bot: Bot):
    bot.add_cog(BetterMeme(bot))
