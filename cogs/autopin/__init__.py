from .cog import AutoPin


def setup(bot):
    bot.add_cog(AutoPin(bot))
