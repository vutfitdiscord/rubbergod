from disnake.ext.commands import Bot

from .cog import Poll


def setup(bot: Bot):
    bot.add_cog(Poll(bot))
