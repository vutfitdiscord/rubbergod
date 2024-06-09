from rubbergod import Rubbergod

from .cog import Warden


def setup(bot: Rubbergod):
    bot.add_cog(Warden(bot))
