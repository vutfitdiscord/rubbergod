"""
Cog implementing functions for server moderation and help functions for mods.
Implemented logging for tagging @mods.
"""

from datetime import datetime, timezone
from typing import List, Union

import disnake
from disnake.ext import commands

import utils
from buttons.moderation import ModerationView
from cogs.base import Base
from config.messages import Messages
from permissions import permission_check

# Reflects UI slider values
slowmode_delay_timestamps = {
    "5s": 5,
    "10s": 10,
    "15s": 15,
    "30s": 30,
    "1min": 60,
    "2min": 2*60,
    "5min": 5*60,
    "10min": 10*60,
    "15min": 15*60,
    "30min": 30*60,
    "1h": 1*60*60,
    "2h": 2*60*60,
    "6h": 6*60*60
}


async def slowmode_delay_times(inter, string: str) -> List[str]:
    return [delay for delay in slowmode_delay_timestamps.keys() if string.lower() in delay.lower()]

slowmode_channel_type = Union[
    disnake.TextChannel,
    disnake.Thread,
    disnake.VoiceChannel,
    disnake.ForumChannel
]


class Moderation(Base, commands.Cog):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        self.moderation_true = "moderation:resolve:true"
        self.moderation_false = "moderation:resolve:false"

    async def mod_tag(self, message: disnake.Message, title, room):
        if len(message.content) < 3800:
            embed = disnake.Embed(
                title=f"Tagged {title}",
                description=f"**User:** {message.author.mention}\n"
                f"**Link:** [#{message.channel}]({message.jump_url})\n"
                f"**Content:**\n{message.content}",
                color=disnake.Color.yellow()
            )
        else:
            embed = disnake.Embed(
                title=f"Tagged {title}",
                description=f"**User:** {message.author.mention}\n"
                f"**Link:** [#{message.channel}]({message.jump_url})\n",
                color=disnake.Color.yellow()
            )
            parts = utils.split_to_parts(message.content, 1024)
            for msg in parts:
                embed.add_field(name="Content", value=msg, inline=False)

        embed.add_field(name="Resolved by:", value="---")
        embed.set_footer(text=datetime.now().strftime('%d.%m.%Y %H:%M'))
        await room.send(
            embed=embed,
            view=ModerationView("Resolve", self.moderation_false)
        )

    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message):
        """Logs use of @mod, @submod and @helper tag and send message to designated room"""

        for role in message.role_mentions:
            if role.id == self.config.mod_role:
                await self.mod_tag(message, "@mod", self.mod_room)
                return

            elif role.id in [self.config.submod_role, self.config.helper_role]:
                await self.mod_tag(message, "@submod/@helper", self.submod_helper_room)
                return

    @commands.Cog.listener()
    async def on_button_click(self, inter: disnake.MessageInteraction):
        if inter.component.custom_id not in [self.moderation_true, self.moderation_false]:
            return

        embed = inter.message.embeds[0].to_dict()
        if inter.component.custom_id == self.moderation_true:
            label = "Resolve"
            custom_id = self.moderation_false
            embed["color"] = disnake.Color.yellow()
            for field in embed["fields"]:
                if field["name"] == "Resolved by:":
                    field["value"] = "---"

        else:
            label = "Unresolve"
            custom_id = self.moderation_true
            embed["color"] = disnake.Color.green()
            for field in embed["fields"]:
                if field["name"] == "Resolved by:":
                    field["value"] = inter.author.mention

        await inter.response.edit_message(
            embed=disnake.Embed.from_dict(embed),
            view=ModerationView(label, custom_id)
        )

    @commands.check(permission_check.submod_plus)
    @commands.slash_command(name="slowmode")
    async def _slowmode(self, inter):
        await inter.response.defer(ephemeral=True)

    @_slowmode.sub_command(name="set", description=Messages.slowmode_set_brief)
    async def set(
        self,
        inter: disnake.ApplicationCommandInteraction,
        delay: int = commands.Param(
            autocomplete=slowmode_delay_timestamps,
            description=Messages.slowmode_time,
            ge=0,
            lt=21600  # Maximum is 6 hours (See discord docs)
        ),
        channel: slowmode_channel_type = None
    ):
        channel = inter.channel if channel is None else channel
        prev_delay = channel.slowmode_delay
        await channel.edit(slowmode_delay=delay)
        await self.log(inter, prev_delay, curr_delay=delay, channel=channel)
        await inter.edit_original_response(Messages.slowmode_set_success(
                                            channel=channel.mention,
                                            delay=delay))

    @commands.check(permission_check.submod_plus)
    @_slowmode.sub_command(name="remove", description=Messages.slowmode_remove_brief)
    async def remove(
        self,
        inter: disnake.ApplicationCommandInteraction,
        channel: slowmode_channel_type = None
    ):
        channel = inter.channel if channel is None else channel
        prev_delay = inter.channel.slowmode_delay
        await channel.edit(slowmode_delay=0)
        await self.log(inter, prev_delay, curr_delay=0, channel=channel)
        await inter.edit_original_response(Messages.slowmode_remove_success(
                                            channel=channel.mention))

    async def log(
        self,
        inter: disnake.ApplicationCommandInteraction,
        prev_delay: int,
        curr_delay: int,
        channel: slowmode_channel_type
    ):
        """
        Log slowmode changes
        """
        embed = disnake.Embed(title="Channel slowmode change", color=disnake.Colour.yellow())
        embed.add_field(
            name="Mod",
            value=f"{inter.author.mention} ({inter.author.display_name})"
        )
        embed.add_field(
            name="Channel",
            value=f"[#{channel.name}]({channel.jump_url})",
            inline=False
        )
        embed.add_field(
            name="Old value",
            value=f"{prev_delay} seconds"
        )
        embed.add_field(
            name="New value",
            value=f"{curr_delay} seconds"
        )
        embed.timestamp = datetime.now(tz=timezone.utc)
        channel = self.bot.get_channel(self.config.log_channel)
        await channel.send(embed=embed)


def setup(bot):
    bot.add_cog(Moderation(bot))
