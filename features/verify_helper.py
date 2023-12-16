from disnake import Member
from disnake.ext.commands import Bot

import utils
from config.app_config import config


class VerifyHelper:
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    async def has_role(self, user, role_name: str) -> bool:
        if isinstance(user, Member):
            return utils.has_role(user, role_name)
        else:
            guild = await self.bot.fetch_guild(config.guild_id)
            member = await guild.fetch_member(user.id)
            return utils.has_role(member, role_name)
