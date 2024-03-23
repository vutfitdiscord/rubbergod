from disnake.ext.commands import Bot

from .cog import ContestVote


def setup(bot: Bot):
    bot.add_cog(ContestVote(bot))
