from disnake.ext.commands import Bot

from .cog import Week


def setup(bot: Bot):
    bot.add_cog(Week(bot))
