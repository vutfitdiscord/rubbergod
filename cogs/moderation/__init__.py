from disnake.ext.commands import Bot

from .cog import Moderation


def setup(bot: Bot):
    bot.add_cog(Moderation(bot))
