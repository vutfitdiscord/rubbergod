from rubbergod import Rubbergod

from .cog import ScamGuard


def setup(bot: Rubbergod):
    bot.add_cog(ScamGuard(bot))
