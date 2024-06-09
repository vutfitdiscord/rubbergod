from rubbergod import Rubbergod

from .cog import IOS


def setup(bot: Rubbergod):
    bot.add_cog(IOS(bot))
