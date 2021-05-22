from discord.ext import commands
from config import app_config as config, cooldowns
from features import verification
from repository import user_repo
from config.messages import Messages


user_r = user_repo.UserRepository()

config = config.Config


class Verify(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.verification = verification.Verification(bot, user_r)

    @cooldowns.default_cooldown
    @commands.command(brief=Messages.verify_brief)
    async def verify(self, ctx):
        await self.verification.verify(ctx.message)

    @cooldowns.default_cooldown
    @commands.command(brief=Messages.get_code_brief)
    async def getcode(self, ctx):
        await self.verification.send_code(ctx.message)


def setup(bot):
    bot.add_cog(Verify(bot))
