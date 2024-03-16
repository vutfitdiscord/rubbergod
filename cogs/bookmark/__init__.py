from .cog import Bookmark


def setup(bot):
    bot.add_cog(Bookmark(bot))
