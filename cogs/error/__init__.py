from rubbergod import Rubbergod

from .cog import Error


def setup(bot: Rubbergod):
    bot.add_cog(Error(bot))
