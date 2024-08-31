from datetime import datetime, timezone
from typing import TypeAlias

import disnake

import utils

from .views import View

SLOWMODE_CHANNEL_TYPES: TypeAlias = (
    disnake.TextChannel | disnake.Thread | disnake.VoiceChannel | disnake.ForumChannel
)

MODERATION_TRUE = "moderation:resolve:true"
MODERATION_FALSE = "moderation:resolve:false"


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


async def slowmode_delay_autocomp(
    inter: disnake.ApplicationCommandInteraction, string: str
) -> dict[str, int]:
    return {key: value for key, value in delay_timestamps.items() if string.lower() in key.lower()}


async def mod_tag(message: disnake.Message, role: str, room: disnake.TextChannel):
    if len(message.content) < 3800:
        embed = disnake.Embed(
            title=f"Tagged {role}",
            description=f"**User:** {message.author.mention}\n"
            f"**Link:** [#{message.channel}]({message.jump_url})\n"
            f"**Content:**\n{message.content}",
            color=disnake.Color.yellow(),
        )
    else:
        embed = disnake.Embed(
            title=f"Tagged {role}",
            description=f"**User:** {message.author.mention}\n"
            f"**Link:** [#{message.channel}]({message.jump_url})\n",
            color=disnake.Color.yellow(),
        )
        parts = utils.general.split_to_parts(message.content, 1024)
        for msg in parts:
            embed.add_field(name="Content", value=msg, inline=False)

    embed.add_field(name="Resolved by:", value="---")
    embed.set_footer(text=datetime.now().strftime("%d.%m.%Y %H:%M"))
    await room.send(embed=embed, view=View("Resolve", MODERATION_FALSE))


async def log(
    inter: disnake.GuildCommandInteraction,
    prev_delay: int,
    curr_delay: int,
    channel: SLOWMODE_CHANNEL_TYPES,
    log_channel: disnake.TextChannel,
):
    """
    Log slowmode changes
    """
    embed = disnake.Embed(title="Channel slowmode change", color=disnake.Colour.yellow())
    embed.add_field(name="Mod", value=f"{inter.author.mention} ({inter.author.name})")
    embed.add_field(name="Channel", value=f"[#{channel.name}]({channel.jump_url})", inline=False)
    embed.add_field(name="Old value", value=f"{prev_delay} seconds")
    embed.add_field(name="New value", value=f"{curr_delay} seconds")
    embed.timestamp = datetime.now(tz=timezone.utc)
    await log_channel.send(embed=embed)
