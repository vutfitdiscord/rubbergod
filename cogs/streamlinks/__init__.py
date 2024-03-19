from disnake.ext.commands import Bot

from .cog import StreamLinks


def setup(bot: Bot):
    bot.add_cog(StreamLinks(bot))
