from disnake.ext.commands import Bot

from .cog import Verify


def setup(bot: Bot):
    bot.add_cog(Verify(bot))
