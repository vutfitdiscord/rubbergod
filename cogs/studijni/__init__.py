from disnake.ext.commands import Bot

from .cog import Studijni


def setup(bot: Bot):
    bot.add_cog(Studijni(bot))
