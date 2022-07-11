import disnake
import utils
from features.base_feature import BaseFeature
from disnake.ext.commands import Bot
from features.verification import Verification
from repository.database.verification import DynamicVerifyRule
from repository.user_repo import UserRepository
from repository.verify_repo import VerifyRepository
from typing import Union
from config.app_config import config
from config.messages import Messages


class DynamicVerifyManager(BaseFeature):
    def __init__(self, bot: Bot) -> None:
        super().__init__(bot)
        self.user_repo = UserRepository()
        self.verify_repo = VerifyRepository()
        self.verification = Verification(bot)

    async def can_apply_rule(self, user: Union[disnake.User, disnake.Member], rule_id: str) -> bool:
        return self.verify_repo.exists_rule(rule_id) and not await self.verification.has_role(
            user, config.verification_role
        )

    async def apply_rule(self, rule_id: str, inter: disnake.ApplicationCommandInteraction) -> None:
        guild = inter.guild if inter.guild is not None else await self.bot.get_guild(config.guild_id)
        rule = self.verify_repo.get_rule(rule_id)
        role_ids = rule.get_role_ids()
        roles = [guild.get_role(role_id) for role_id in role_ids]
        await self.log_attempt(rule, inter)
        member = await guild.get_or_fetch_member(inter.user.id)
        await member.add_roles(roles=roles, reason="Rubbergod dynamic verification")

        try:
            await member.send(utils.fill_message("verify_verify_success", user=inter.user.id))
            await member.send(Messages.verify_post_verify_info)
        except disnake.HTTPException:
            pass  # User maybe have disabled communication with bots.

        if inter.channel.type is not disnake.ChannelType.private:
            await inter.send(utils.fill_message("verify_verify_success", user=inter.user.id))

    async def log_attempt(
        self, rule: DynamicVerifyRule, inter: disnake.ApplicationCommandInteraction
    ) -> None:
        embed = disnake.Embed(title="Dynamická verifikace", color=0xEEE657)
        embed.add_field("Pravidlo", f"{rule.name} ({rule.id})")
        embed.add_field(
            "Uživatel",
            f"{inter.user.name}#{inter.user.discriminator} ({utils.generate_mention(inter.user.id)})",
        )

        channel = self.bot.get_channel(config.log_channel)
        await channel.send(embed=embed)
