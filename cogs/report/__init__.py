from disnake.ext.commands import Bot

from .cog import Report


def setup(bot: Bot):
    bot.add_cog(Report(bot))
