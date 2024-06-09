from rubbergod import Rubbergod

from .cog import Icons


def setup(bot: Rubbergod):
    bot.add_cog(Icons(bot))
