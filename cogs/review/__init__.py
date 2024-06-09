from rubbergod import Rubbergod

from .cog import Review


def setup(bot: Rubbergod):
    bot.add_cog(Review(bot))
