from disnake.ext.commands import Bot

from .cog import Subscriptions


def setup(bot: Bot):
    bot.add_cog(Subscriptions(bot))
