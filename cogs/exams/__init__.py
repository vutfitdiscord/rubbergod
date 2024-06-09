from rubbergod import Rubbergod

from .cog import Exams


def setup(bot: Rubbergod):
    bot.add_cog(Exams(bot))
