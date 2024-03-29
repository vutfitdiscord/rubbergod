from disnake.ext.commands import Bot

from .cog import FitWide


def setup(bot: Bot):
    bot.add_cog(FitWide(bot))
