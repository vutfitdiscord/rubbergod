from .streamlinks import StreamLinks


def setup(bot):
    bot.add_cog(StreamLinks(bot))
