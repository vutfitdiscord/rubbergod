from rubbergod import Rubbergod

from .cog import GrillbotApi


def setup(bot: Rubbergod):
    bot.add_cog(GrillbotApi(bot))
