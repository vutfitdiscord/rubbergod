from rubbergod import Rubbergod

from .cog import Message


def setup(bot: Rubbergod):
    bot.add_cog(Message(bot))
