import datetime

import discord
from discord.ext import commands

import utils
from config import config, messages

config = config.Config
messages = messages.Messages


class Kachna(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def kachna(self, ctx):
        await ctx.send(messages.kachna_grillbot)


def setup(bot):
    bot.add_cog(Kachna(bot))
