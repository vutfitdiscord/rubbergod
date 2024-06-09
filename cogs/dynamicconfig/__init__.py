from rubbergod import Rubbergod

from .cog import DynamicConfig


def setup(bot: Rubbergod):
    bot.add_cog(DynamicConfig(bot))
