from disnake.ext.commands import Bot

from .cog import AutoPin


def setup(bot: Bot):
    bot.add_cog(AutoPin(bot))
