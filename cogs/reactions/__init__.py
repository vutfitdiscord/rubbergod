from disnake.ext.commands import Bot

from .cog import Reactions


def setup(bot: Bot):
    bot.add_cog(Reactions(bot))
