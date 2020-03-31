import discord
from discord.ext import commands

from config import config

config = config.Config


class Warphole(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.sibling = self.bot.get_user(config.warphole_sibling_id)
        self.warp_channel = self.bot.get_channel(config.warphole_channel_id)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.channel == self.warp_channel:
            self.sibling.send(discord.utils.escape_mentions(message.content))
        elif (isinstance(message.channel, discord.DMChannel) and
              message.channel.recipient == self.sibling):
            self.warp_channel.send(message.content)


def setup(bot):
    bot.add_cog(Warphole(bot))
