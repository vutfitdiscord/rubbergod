from disnake.ext.commands import Bot

from .cog import IOS


def setup(bot: Bot):
    bot.add_cog(IOS(bot))
