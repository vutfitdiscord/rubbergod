from rubbergod import Rubbergod

from .cog import Moderation


def setup(bot: Rubbergod):
    bot.add_cog(Moderation(bot))
