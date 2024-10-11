"""
Cog implementing functions for server moderation and help functions for mods.
Implemented logging for tagging @mods.
"""

import disnake
from disnake.ext import commands

from cogs.base import Base
from database.moderation import ActionType, ModerationDB
from permissions.checks import PermissionsCheck
from rubbergod import Rubbergod
from utils.colors import RubbergodColors

from . import features
from .features import MODERATION_FALSE, MODERATION_TRUE, SLOWMODE_CHANNEL_TYPES
from .messages_cz import MessagesCZ
from .views import View


class Moderation(Base, commands.Cog):
    def __init__(self, bot: Rubbergod):
        super().__init__()
        self.bot = bot

    @PermissionsCheck.is_submod_plus()
    @commands.slash_command(name="slowmode")
    async def _slowmode(self, inter: disnake.AppCommandInteraction):
        await inter.response.defer(ephemeral=True)

    @_slowmode.sub_command(name="set", description=MessagesCZ.set_brief)
    async def set(
        self,
        inter: disnake.GuildCommandInteraction,
        delay: int = commands.Param(
            autocomplete=features.slowmode_delay_autocomp,
            description=MessagesCZ.time_param,
            ge=0,
            lt=21600,  # Maximum is 6 hours (See discord docs)
        ),
        channel: SLOWMODE_CHANNEL_TYPES = None,
    ):
        if channel is None:
            channel = inter.channel
        prev_delay = channel.slowmode_delay
        await channel.edit(slowmode_delay=delay)
        await features.log(inter, prev_delay, curr_delay=delay, channel=channel, log_channel=self.log_channel)
        await inter.edit_original_response(MessagesCZ.set_success(channel=channel.mention, delay=delay))

    @PermissionsCheck.is_submod_plus()
    @_slowmode.sub_command(name="remove", description=MessagesCZ.remove_brief)
    async def remove(self, inter: disnake.GuildCommandInteraction, channel: SLOWMODE_CHANNEL_TYPES = None):
        if channel is None:
            channel = inter.channel
        prev_delay = inter.channel.slowmode_delay
        await channel.edit(slowmode_delay=0)
        await features.log(inter, prev_delay, curr_delay=0, channel=channel, log_channel=self.log_channel)
        await inter.edit_original_response(MessagesCZ.remove_success(channel=channel.mention))

    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message):
        """Logs use of @mod, @submod and @helper tag and send message to designated room"""

        for role in message.role_mentions:
            if role.id == self.config.mod_role:
                await features.mod_tag(message, "@mod", self.mod_room)
                return

            elif role.id in [self.config.submod_role, self.config.helper_role]:
                await features.mod_tag(message, "@submod/@helper", self.submod_helper_room)
                return

    @commands.Cog.listener()
    async def on_button_click(self, inter: disnake.MessageInteraction):
        if inter.component.custom_id not in [MODERATION_TRUE, MODERATION_FALSE]:
            return

        embed = inter.message.embeds[0].to_dict()
        if inter.component.custom_id == MODERATION_TRUE:
            label = "Resolve"
            custom_id = MODERATION_FALSE
            embed["color"] = RubbergodColors.yellow()
            for field in embed["fields"]:
                if field["name"] == "Resolved by:":
                    field["value"] = "---"

        else:
            label = "Unresolve"
            custom_id = MODERATION_TRUE
            embed["color"] = RubbergodColors.green()
            for field in embed["fields"]:
                if field["name"] == "Resolved by:":
                    field["value"] = inter.author.mention

        await inter.response.edit_message(embed=disnake.Embed.from_dict(embed), view=View(label, custom_id))

    @commands.Cog.listener()
    async def on_audit_log_entry_create(self, entry: disnake.AuditLogEntry):
        if entry.guild.id != self.config.guild_id:
            return

        if entry.action not in (
            disnake.AuditLogAction.kick,
            disnake.AuditLogAction.ban,
            disnake.AuditLogAction.unban,
        ):
            # We only care about kicks and (un)bans
            return

        if entry.action == disnake.AuditLogAction.kick:
            action_emoji = "👢"
            action_name = "kicked"
            action_type = ActionType.kick
        elif entry.action == disnake.AuditLogAction.ban:
            action_emoji = "🔨"
            action_name = "banned"
            action_type = ActionType.ban
        elif entry.action == disnake.AuditLogAction.unban:
            action_emoji = "🔓"
            action_name = "unbanned"
            action_type = ActionType.unban

        timestamp = disnake.utils.format_dt(entry.created_at)

        target = entry.target
        if isinstance(target, disnake.Object):
            target = await self.bot.fetch_user(target.id)

        content = MessagesCZ.moderation_log(
            entry=entry, target=target, action_emoji=action_emoji, action=action_name, timestamp=timestamp
        )

        flags = disnake.MessageFlags(suppress_notifications=True)
        ModerationDB.add_action_log(
            target_id=target.id,
            author_id=entry.user.id,
            datetime=entry.created_at,
            reason=entry.reason,
            action_type=action_type,
        )
        await self.moderation_channel.send(content=content, flags=flags)
