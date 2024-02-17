"""
Cog for managing server emojis. Download emojis and stickers. Get full size of emoji.\
"""

import io
import os
import zipfile
from datetime import time

import disnake
from disnake.ext import commands, tasks

import utils
from cogs.base import Base
from config import cooldowns
from config.messages import Messages
from permissions import room_check


class Emoji(Base, commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check = room_check.RoomCheck(bot)
        self.tasks = [self.download_emojis_task.start()]

    async def download_emojis(self, guild: disnake.Guild):
        """Download all emojis from server and save them to zip file"""
        emojis = await guild.fetch_emojis()
        stickers = await guild.fetch_stickers()
        with zipfile.ZipFile('emojis.zip', 'w') as zip_file:
            for emoji in emojis:
                with io.BytesIO() as image_binary:
                    if emoji.animated:
                        emoji_name = f'emojis/{emoji.name}.gif'
                    else:
                        emoji_name = f'emojis/{emoji.name}.png'
                    await emoji.save(image_binary)
                    zip_file.writestr(emoji_name, image_binary.getvalue())

            for sticker in stickers:
                with io.BytesIO() as image_binary:
                    sticker_name = f'stickers/{sticker.name}.{sticker.format.name}'
                    await sticker.save(image_binary)
                    zip_file.writestr(sticker_name, image_binary.getvalue())

    @cooldowns.default_cooldown
    @commands.slash_command(name='emoji')
    async def emoji(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer(ephemeral=self.check.botroom_check(inter))

    @cooldowns.default_cooldown
    @emoji.sub_command(name='get_emojis', description=Messages.emoji_get_emojis_brief)
    async def get_emojis(self, inter: disnake.ApplicationCommandInteraction):
        """Get all emojis from server"""
        if not os.path.exists('emojis.zip'):
            await self.download_emojis(self.base_guild)
        await inter.send(file=disnake.File('emojis.zip'))

    @cooldowns.default_cooldown
    @emoji.sub_command(name='get_emoji', description=Messages.emoji_get_emoji_brief)
    async def get_emoji(self, inter: disnake.ApplicationCommandInteraction, emoji: disnake.PartialEmoji):
        """Get emoji in full size"""
        await inter.send(emoji.url)

    @tasks.loop(time=time(5, 0, tzinfo=utils.get_local_zone()))
    async def download_emojis_task(self):
        await self.download_emojis(self.base_guild)

    @get_emoji.error
    async def emoji_errors(self, inter: disnake.ApplicationCommandInteraction, error):
        if isinstance(error, commands.PartialEmojiConversionFailure):
            await inter.send(Messages.emoji_not_emoji, ephemeral=True)
            return True


def setup(bot):
    bot.add_cog(Emoji(bot))
