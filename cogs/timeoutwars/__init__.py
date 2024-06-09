from rubbergod import Rubbergod

from .cog import TimeoutWars


def setup(bot: Rubbergod):
    bot.add_cog(TimeoutWars(bot))
