"""
Cog implementing functions for server moderation and help functions for mods.
Implemented logging for tagging @mods.
"""

import disnake
from disnake.ext import commands

from cogs.base import Base
from permissions import permission_check

from . import features
from .features import MODERATION_FALSE, MODERATION_TRUE, SLOWMODE_CHANNEL_TYPES
from .messages_cz import MessagesCZ
from .views import View

# Reflects UI slider values
delay_timestamps = {
    "5s": 5,
    "10s": 10,
    "15s": 15,
    "30s": 30,
    "1min": 60,
    "2min": 2 * 60,
    "5min": 5 * 60,
    "10min": 10 * 60,
    "15min": 15 * 60,
    "30min": 30 * 60,
    "1h": 1 * 60 * 60,
    "2h": 2 * 60 * 60,
    "6h": 6 * 60 * 60,
}


async def slowmode_delay_times(inter: disnake.ApplicationCommandInteraction, string: str) -> list[str]:
    return [delay for delay in delay_timestamps.keys() if string.lower() in delay.lower()]


class Moderation(Base, commands.Cog):
    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot

    @commands.check(permission_check.submod_plus)
    @commands.slash_command(name="slowmode")
    async def _slowmode(self, inter: disnake.AppCommandInteraction):
        await inter.response.defer(ephemeral=True)

    @_slowmode.sub_command(name="set", description=MessagesCZ.set_brief)
    async def set(
        self,
        inter: disnake.GuildCommandInteraction,
        delay: int = commands.Param(
            autocomplete=delay_timestamps,
            description=MessagesCZ.time_param,
            ge=0,
            lt=21600,  # Maximum is 6 hours (See discord docs)
        ),
        channel: SLOWMODE_CHANNEL_TYPES = None,
    ):
        channel = inter.channel if channel is None else channel
        prev_delay = channel.slowmode_delay
        await channel.edit(slowmode_delay=delay)
        await features.log(inter, prev_delay, curr_delay=delay, channel=channel, log_channel=self.log_channel)
        await inter.edit_original_response(MessagesCZ.set_success(channel=channel.mention, delay=delay))

    @commands.check(permission_check.submod_plus)
    @_slowmode.sub_command(name="remove", description=MessagesCZ.remove_brief)
    async def remove(self, inter: disnake.GuildCommandInteraction, channel: SLOWMODE_CHANNEL_TYPES = None):
        channel = inter.channel if channel is None else channel
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
            embed["color"] = disnake.Color.yellow()
            for field in embed["fields"]:
                if field["name"] == "Resolved by:":
                    field["value"] = "---"

        else:
            label = "Unresolve"
            custom_id = MODERATION_TRUE
            embed["color"] = disnake.Color.green()
            for field in embed["fields"]:
                if field["name"] == "Resolved by:":
                    field["value"] = inter.author.mention

        await inter.response.edit_message(embed=disnake.Embed.from_dict(embed), view=View(label, custom_id))
