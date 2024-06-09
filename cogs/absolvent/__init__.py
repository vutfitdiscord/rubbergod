from rubbergod import Rubbergod

from .cog import Absolvent


def setup(bot: Rubbergod):
    bot.add_cog(Absolvent(bot))
