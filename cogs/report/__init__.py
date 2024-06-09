from rubbergod import Rubbergod

from .cog import Report


def setup(bot: Rubbergod):
    bot.add_cog(Report(bot))
