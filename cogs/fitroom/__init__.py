from rubbergod import Rubbergod

from .cog import FitRoom


def setup(bot: Rubbergod):
    bot.add_cog(FitRoom(bot))
