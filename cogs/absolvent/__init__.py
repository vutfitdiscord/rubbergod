from disnake.ext.commands import Bot

from .cog import Absolvent


def setup(bot: Bot):
    bot.add_cog(Absolvent(bot))
