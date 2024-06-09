from rubbergod import Rubbergod

from .cog import Help


def setup(bot: Rubbergod):
    bot.add_cog(Help(bot))
