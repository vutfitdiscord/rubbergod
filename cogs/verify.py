from disnake.ext import commands
from config import cooldowns
from features import verification
from config.messages import Messages
import disnake
from config.app_config import config
from features.dynamic_verify import DynamicVerifyManager


class Verify(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.verification = verification.Verification(bot)
        self.dynamic_verify = DynamicVerifyManager(bot)

    def is_valid_guild(ctx: disnake.ApplicationCommandInteraction) -> bool:
        return ctx.guild_id is None or ctx.guild_id == config.guild_id

    @cooldowns.default_cooldown
    @commands.check(is_valid_guild)
    @commands.slash_command(name="verify", description=Messages.verify_brief, dm_permission=True)
    async def verify(
        self,
        inter: disnake.ApplicationCommandInteraction,
        login: str = commands.Param(description=Messages.verify_login_parameter),
    ):
        if await self.dynamic_verify.can_apply_rule(inter.user, login):
            await self.dynamic_verify.apply_rule(login, inter)
            return
        await self.verification.clear_host_roles(inter)
        await self.verification.send_code(login, inter)

    @verify.error
    async def on_verification_error(self, inter: disnake.ApplicationCommandInteraction, error):
        if isinstance(error, commands.CheckFailure):
            await inter.send(Messages.verify_invalid_channel, ephemeral=True)
            return True


def setup(bot):
    bot.add_cog(Verify(bot))
