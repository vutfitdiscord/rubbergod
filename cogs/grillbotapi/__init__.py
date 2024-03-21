from disnake.ext.commands import Bot

from .cog import GrillbotApi


def setup(bot: Bot):
    bot.add_cog(GrillbotApi(bot))
