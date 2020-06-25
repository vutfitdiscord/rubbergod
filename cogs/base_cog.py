from discord.ext.commands import Bot
from discord.ext import commands

import utils
from config import config


class BaseCog(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.config = config.Config

    async def validate_admin_rights(self, ctx: commands.Context) -> bool:
        if ctx.author.id != self.config.admin_id:
            await ctx.send(utils.fill_message("insufficient_rights", user=ctx.author.id))
            return False

        return True
