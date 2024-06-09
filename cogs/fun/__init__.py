from rubbergod import Rubbergod

from .cog import Fun


def setup(bot: Rubbergod):
    bot.add_cog(Fun(bot))
