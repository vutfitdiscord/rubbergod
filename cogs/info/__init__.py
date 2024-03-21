from disnake.ext.commands import Bot

from .cog import Info


def setup(bot: Bot):
    bot.add_cog(Info(bot))
