from disnake.ext.commands import Bot

from .cog import Error


def setup(bot: Bot):
    bot.add_cog(Error(bot))
