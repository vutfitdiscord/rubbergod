from disnake.ext.commands import Bot

from .cog import Message


def setup(bot: Bot):
    bot.add_cog(Message(bot))
