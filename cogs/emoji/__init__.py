from .cog import Emoji


def setup(bot):
    bot.add_cog(Emoji(bot))
