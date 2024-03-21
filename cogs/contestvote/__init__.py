from .cog import ContestVote


def setup(bot):
    bot.add_cog(ContestVote(bot))
