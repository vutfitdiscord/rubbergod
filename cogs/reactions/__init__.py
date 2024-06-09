from rubbergod import Rubbergod

from .cog import Reactions


def setup(bot: Rubbergod):
    bot.add_cog(Reactions(bot))
