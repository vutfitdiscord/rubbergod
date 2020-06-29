from discord.ext import commands
from config import messages

messages = messages.Messages


class Kachna(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def kachna(self, ctx):
        await ctx.send(messages.kachna_grillbot)


def setup(bot):
    bot.add_cog(Kachna(bot))
