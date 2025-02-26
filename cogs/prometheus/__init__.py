from rubbergod import Rubbergod

from .cog import Prometheus


def setup(bot: Rubbergod):
    bot.add_cog(Prometheus(bot))
