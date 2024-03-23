from disnake.ext.commands import Bot

from .cog import DynamicConfig


def setup(bot: Bot):
    bot.add_cog(DynamicConfig(bot))
