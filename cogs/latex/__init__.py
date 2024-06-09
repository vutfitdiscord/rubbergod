from rubbergod import Rubbergod

from .cog import Latex


def setup(bot: Rubbergod):
    bot.add_cog(Latex(bot))
