from disnake.ext.commands import Bot

from .cog import Fun


def setup(bot: Bot):
    bot.add_cog(Fun(bot))
