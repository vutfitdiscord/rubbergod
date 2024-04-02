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
        parts = utils.split_to_parts(message.content, 1024)
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
