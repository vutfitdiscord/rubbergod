from rubbergod import Rubbergod

from .cog import Timeout


def setup(bot: Rubbergod):
    bot.add_cog(Timeout(bot))
