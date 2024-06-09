from rubbergod import Rubbergod

from .cog import AutoPin


def setup(bot: Rubbergod):
    bot.add_cog(AutoPin(bot))
