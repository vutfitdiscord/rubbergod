from rubbergod import Rubbergod

from .cog import Emoji


def setup(bot: Rubbergod):
    bot.add_cog(Emoji(bot))
