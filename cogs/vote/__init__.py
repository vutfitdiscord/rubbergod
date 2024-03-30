from disnake.ext.commands import Bot

from .cog import Vote


def setup(bot: Bot):
    bot.add_cog(Vote(bot))
