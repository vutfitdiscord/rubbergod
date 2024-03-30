from disnake.ext.commands import Bot

from .cog import Warden


def setup(bot: Bot):
    bot.add_cog(Warden(bot))
