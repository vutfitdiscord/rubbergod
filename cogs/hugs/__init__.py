from disnake.ext.commands import Bot

from .cog import Hugs


def setup(bot: Bot):
    bot.add_cog(Hugs(bot))
