import utils
from disnake import Member
from config.app_config import config


class VerifyHelper:
    async def has_role(self, user, role_name: str) -> bool:
        if type(user) == Member:
            return utils.has_role(user, role_name)
        else:
            guild = await self.bot.fetch_guild(config.guild_id)
            member = await guild.fetch_member(user.id)
            return utils.has_role(member, role_name)
