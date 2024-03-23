from disnake.ext.commands import Bot

from .cog import Exams


def setup(bot: Bot):
    bot.add_cog(Exams(bot))
