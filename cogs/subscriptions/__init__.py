from rubbergod import Rubbergod

from .cog import Subscriptions


def setup(bot: Rubbergod):
    bot.add_cog(Subscriptions(bot))
