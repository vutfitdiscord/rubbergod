from rubbergod import Rubbergod

from .cog import ContestVote


def setup(bot: Rubbergod):
    bot.add_cog(ContestVote(bot))
