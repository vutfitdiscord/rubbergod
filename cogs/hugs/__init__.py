from rubbergod import Rubbergod

from .cog import Hugs


def setup(bot: Rubbergod):
    bot.add_cog(Hugs(bot))
