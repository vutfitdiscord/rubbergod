import discord
from discord.ext import commands

from config import config

config = config.Config


class Warphole(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.warp_channel_blue = self.bot.get_channel(config.warphole_blue)
        self.warp_channel_orange = self.bot.get_channel(config.warphole_orange)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        if message.channel == self.warp_channel_blue:
            await self.warp_channel_orange.send(
                    discord.utils.escape_mentions(message.content))
        elif message.channel == self.warp_channel_orange:
            await self.warp_channel_blue.send(
                    discord.utils.escape_mentions(message.content))


def setup(bot):
    bot.add_cog(Warphole(bot))
