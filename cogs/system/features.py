import os

import disnake
from disnake.ext import commands
from genericpath import isdir, isfile

import utils
from config.app_config import config

from . import features
from .messages_cz import MessagesCZ


def get_all_cogs() -> list[tuple[str, str]]:
    """Get all cog modules

    Returns:
    --------
    List of tuples with cog name and path
    """
    path = "./cogs"
    all_cogs = []

    for name in os.listdir(path):
        if not isdir(f"{path}/{name}"):
            continue

        if not isfile(f"{path}/{name}/__init__.py"):
            continue

        all_cogs.append((name, f"{path}/{name}"))

    return sorted(all_cogs)


async def split_cogs() -> list[list[tuple[str, str]]]:
    """Slices list of all cogs to chunks for select.

    Returns:
    --------
    List of tuples with cog name and path
    """
    cog_pairs = get_all_cogs()
    all_cogs = []
    pairs_count = len(cog_pairs)
    chunk_size = 25

    for i in range(0, len(cog_pairs), chunk_size):
        pairs = cog_pairs[i : min(i + chunk_size, pairs_count)]
        all_cogs.append(pairs)

    return all_cogs


def create_embed(bot: commands.Bot) -> disnake.Embed:
    """Create embed with all cogs and statuses."""
    embed = disnake.Embed(title=MessagesCZ.embed_title, colour=disnake.Color.yellow())
    bot_cogs = [cog.lower() for cog in bot.cogs]
    cogs = features.get_all_cogs()
    cog_count = len(cogs)

    cog_loaded = []
    cog_unloaded = []
    for cog_name, _ in cogs:
        name = cog_name.title()
        if cog_name in bot_cogs:
            if cog_name not in config.extensions:
                name = f"**{name}**"
            cog_loaded.append(f"✅ {name}\n\n")
        else:
            if cog_name in config.extensions:
                name = f"**{name}**"
            cog_unloaded.append(f"❌ {name}\n\n")

    loaded_count = len(cog_loaded)
    unloaded_count = len(cog_unloaded)

    embed.description = MessagesCZ.embed_description(
        loaded=loaded_count, unloaded=unloaded_count, all=cog_count
    )

    chunks_count = 2 if cog_count <= 20 else 3

    loaded_chunks = utils.split(cog_loaded, chunks_count)
    unloaded_chunks = utils.split(cog_unloaded, chunks_count)

    for loaded_chunk in loaded_chunks:
        embed.add_field(name="\u200b", value="".join(loaded_chunk), inline=True)

    # separator
    if unloaded_chunks:
        embed.add_field(name="\u200b", value="", inline=False)

    for unloaded_chunk in unloaded_chunks:
        embed.add_field(name="\u200b", value="".join(unloaded_chunk), inline=True)

    embed.set_footer(text=MessagesCZ.override)
    return embed
