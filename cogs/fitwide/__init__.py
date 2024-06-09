from rubbergod import Rubbergod

from .cog import FitWide


def setup(bot: Rubbergod):
    bot.add_cog(FitWide(bot))
