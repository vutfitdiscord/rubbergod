from disnake.ext.commands import Bot

from .cog import System


def setup(bot: Bot):
    bot.add_cog(System(bot))
