"""
Cog for managing server emojis. Download emojis and stickers. Get full size of emoji.
"""

import io
import os
import zipfile
from datetime import time

import disnake
from disnake.ext import commands, tasks

import utils
from cogs.base import Base
from rubbergod import Rubbergod
from utils import cooldowns
from utils.checks import PermissionsCheck

from .messages_cz import MessagesCZ


class Emoji(Base, commands.Cog):
    def __init__(self, bot: Rubbergod):
        self.bot = bot
        self.tasks = [self.download_emojis_task.start()]
        self.guild_folder = "guilds"

    async def download_emojis(self, guild: disnake.Guild):
        """Download all emojis from server and save them to zip file"""
        folder_path = f"{self.guild_folder}/{guild.name}"
        file_path = f"{folder_path}/emojis.zip"
        emojis = await guild.fetch_emojis()
        stickers = await guild.fetch_stickers()

        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        with zipfile.ZipFile(file_path, "w") as zip_file:
            for emoji in emojis:
                with io.BytesIO() as image_binary:
                    if emoji.animated:
                        emoji_name = f"emojis/{emoji.name}.gif"
                    else:
                        emoji_name = f"emojis/{emoji.name}.png"
                    await emoji.save(image_binary)
                    zip_file.writestr(emoji_name, image_binary.getvalue())

            for sticker in stickers:
                with io.BytesIO() as image_binary:
                    sticker_name = f"stickers/{sticker.name}.{sticker.format.name}"
                    await sticker.save(image_binary)
                    zip_file.writestr(sticker_name, image_binary.getvalue())

    @cooldowns.default_cooldown
    @commands.slash_command(name="emoji")
    async def emoji(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer(ephemeral=PermissionsCheck.is_botroom(inter))

    @cooldowns.default_cooldown
    @commands.guild_only()
    @emoji.sub_command(name="all", description=MessagesCZ.emoji_all_brief)
    async def get_emojis(self, inter: disnake.ApplicationCommandInteraction):
        """Get all emojis from server"""
        file_path = f"{self.guild_folder}/{inter.guild.name}/emojis.zip"
        if not os.path.exists(file_path):
            await self.download_emojis(inter.guild)
        await inter.send(file=disnake.File(file_path))

    @cooldowns.default_cooldown
    @emoji.sub_command(name="get", description=MessagesCZ.emoji_get_brief)
    async def get_emoji(self, inter: disnake.ApplicationCommandInteraction, emoji: disnake.PartialEmoji):
        """Get emoji in full size"""
        await inter.send(emoji.url)

    @tasks.loop(time=time(5, 0, tzinfo=utils.general.get_local_zone()))
    async def download_emojis_task(self):
        for guild in self.bot.guilds:
            await self.download_emojis(guild)

    @get_emoji.error
    async def emoji_errors(self, inter: disnake.ApplicationCommandInteraction, error):
        if isinstance(error, commands.PartialEmojiConversionFailure):
            await inter.send(MessagesCZ.not_emoji, ephemeral=True)
            return True
