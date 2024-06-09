"""
Cog for meme commands.
"""

import disnake
from disnake.ext import commands

from cogs.base import Base
from rubbergod import Rubbergod

from .messages_cz import MessagesCZ

uhoh_counter = 0


class Meme(Base, commands.Cog):
    def __init__(self, bot: Rubbergod):
        super().__init__()
        self.bot = bot

    @commands.slash_command(name="uhoh", description=MessagesCZ.uhoh_brief)
    async def uhoh(self, inter: disnake.ApplicationCommandInteraction):
        await inter.send(MessagesCZ.uhoh_counter(uhohs=uhoh_counter))

    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message):
        global uhoh_counter

        if message.author.bot:
            if (
                message.author.id in self.config.grillbot_ids
                and message.content.startswith("<:")
                and message.content.endswith(">")
            ):
                await message.channel.send(message.content)
            return

        elif self.config.uhoh_string in message.content.lower():
            await message.channel.send("uh oh")
            uhoh_counter += 1
        elif message.content == "PR":
            await message.channel.send(MessagesCZ.pr_meme)

    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload: disnake.RawMessageDeleteEvent):
        if payload.channel_id == self.config.upgraded_pocitani_thread_id:
            pocitani = self.bot.get_channel(payload.channel_id)
            startnum = self.config.upgraded_pocitani_start_num
            await pocitani.send(MessagesCZ.upgraded_pocitani_caught_deleting)
            await pocitani.send(startnum)
