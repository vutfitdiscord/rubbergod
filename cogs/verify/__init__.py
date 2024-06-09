from rubbergod import Rubbergod

from .cog import Verify


def setup(bot: Rubbergod):
    bot.add_cog(Verify(bot))
