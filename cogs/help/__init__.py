from disnake.ext.commands import Bot

from .cog import Help


def setup(bot: Bot):
    bot.add_cog(Help(bot))
