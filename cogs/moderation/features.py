from datetime import datetime, timezone

import disnake

import utils

from .views import View

SLOWMODE_CHANNEL_TYPES = disnake.TextChannel | disnake.Thread | disnake.VoiceChannel | disnake.ForumChannel


async def mod_tag(self, message: disnake.Message, title, room):
    if len(message.content) < 3800:
        embed = disnake.Embed(
            title=f"Tagged {title}",
            description=f"**User:** {message.author.mention}\n"
            f"**Link:** [#{message.channel}]({message.jump_url})\n"
            f"**Content:**\n{message.content}",
            color=disnake.Color.yellow(),
        )
    else:
        embed = disnake.Embed(
            title=f"Tagged {title}",
            description=f"**User:** {message.author.mention}\n"
            f"**Link:** [#{message.channel}]({message.jump_url})\n",
            color=disnake.Color.yellow(),
        )
        parts = utils.split_to_parts(message.content, 1024)
        for msg in parts:
            embed.add_field(name="Content", value=msg, inline=False)

    embed.add_field(name="Resolved by:", value="---")
    embed.set_footer(text=datetime.now().strftime("%d.%m.%Y %H:%M"))
    await room.send(embed=embed, view=View("Resolve", self.moderation_false))


async def log(
    self,
    inter: disnake.GuildCommandInteraction,
    prev_delay: int,
    curr_delay: int,
    channel: SLOWMODE_CHANNEL_TYPES,
):
    """
    Log slowmode changes
    """
    embed = disnake.Embed(title="Channel slowmode change", color=disnake.Colour.yellow())
    embed.add_field(name="Mod", value=f"{inter.author.mention} ({inter.author.display_name})")
    embed.add_field(name="Channel", value=f"[#{channel.name}]({channel.jump_url})", inline=False)
    embed.add_field(name="Old value", value=f"{prev_delay} seconds")
    embed.add_field(name="New value", value=f"{curr_delay} seconds")
    embed.timestamp = datetime.now(tz=timezone.utc)
    channel = self.bot.get_channel(self.config.log_channel)
    await channel.send(embed=embed)
