from disnake.ext.commands import Bot

from .cog import Roles


def setup(bot: Bot):
    bot.add_cog(Roles(bot))
