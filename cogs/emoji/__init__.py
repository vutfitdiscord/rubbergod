from disnake.ext.commands import Bot

from .cog import Emoji


def setup(bot: Bot):
    bot.add_cog(Emoji(bot))
