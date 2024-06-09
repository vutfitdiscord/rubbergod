from rubbergod import Rubbergod

from .cog import Bookmark


def setup(bot: Rubbergod):
    bot.add_cog(Bookmark(bot))
