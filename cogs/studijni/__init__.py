from rubbergod import Rubbergod

from .cog import Studijni


def setup(bot: Rubbergod):
    bot.add_cog(Studijni(bot))
