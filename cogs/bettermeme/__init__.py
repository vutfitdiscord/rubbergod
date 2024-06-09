from rubbergod import Rubbergod

from .cog import BetterMeme


def setup(bot: Rubbergod):
    bot.add_cog(BetterMeme(bot))
