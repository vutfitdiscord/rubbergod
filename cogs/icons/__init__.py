from disnake.ext.commands import Bot

from .cog import Icons


def setup(bot: Bot):
    bot.add_cog(Icons(bot))
