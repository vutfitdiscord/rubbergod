from rubbergod import Rubbergod

from .cog import Info


def setup(bot: Rubbergod):
    bot.add_cog(Info(bot))
