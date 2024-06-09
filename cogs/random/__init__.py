from rubbergod import Rubbergod

from .cog import Random


def setup(bot: Rubbergod):
    bot.add_cog(Random(bot))
