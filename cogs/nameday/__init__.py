from disnake.ext.commands import Bot

from .cog import Nameday


def setup(bot: Bot):
    bot.add_cog(Nameday(bot))
