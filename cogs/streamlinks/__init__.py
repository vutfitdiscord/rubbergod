from rubbergod import Rubbergod

from .cog import StreamLinks


def setup(bot: Rubbergod):
    bot.add_cog(StreamLinks(bot))
