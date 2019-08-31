from discord.ext import commands
from config import config, messages
from features import verification
from repository import user_repo

user_r = user_repo.UserRepository()

config = config.Config
messages = messages.Messages


class Verify(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.verification = verification.Verification(bot, user_r)

    @commands.cooldown(rate=5, per=30.0, type=commands.BucketType.user)
    @commands.command()
    async def verify(self, ctx):
        await self.verification.verify(ctx.message)

    @commands.cooldown(rate=5, per=30.0, type=commands.BucketType.user)
    @commands.command()
    async def getcode(self, ctx):
        await self.verification.send_code(ctx.message)


def setup(bot):
    bot.add_cog(Verify(bot))
