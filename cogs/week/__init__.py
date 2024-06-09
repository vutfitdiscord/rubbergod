from rubbergod import Rubbergod

from .cog import Week


def setup(bot: Rubbergod):
    bot.add_cog(Week(bot))
