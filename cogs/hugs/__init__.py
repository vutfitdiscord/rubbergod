from .hugs import Hugs


def setup(bot):
    bot.add_cog(Hugs(bot))
