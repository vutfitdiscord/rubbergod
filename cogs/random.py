import random

import discord
from discord.ext import commands

from cogs import room_check
from logic import roll_dice

# Logic (functionality used by features or rubbergod directly)
roll_dice = roll_dice.Roll()


class Random(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check = room_check.RoomCheck(bot)

    @commands.cooldown(rate=5, per=20.0, type=commands.BucketType.user)
    @commands.command()
    async def diceroll(self, ctx, *, arg=""):
        await ctx.send(roll_dice.roll_dice(arg))
        await self.check.botroom_check(ctx.message)

    @commands.cooldown(rate=5, per=20.0, type=commands.BucketType.user)
    @commands.command()
    async def pick(self, ctx, *args):
        """"Pick an option"""
        if not len(args):
            return

        option = discord.utils.escape_mentions(rng.pick_option(args))
        if option:
            await ctx.send("{} {}".format(option, ctx.author.mention))
        await self.check.botroom_check(ctx.message)

    @commands.cooldown(rate=5, per=20.0, type=commands.BucketType.user)
    @commands.command()
    async def flip(self, ctx):
        await ctx.send(random.choice(["True", "False"]))
        await self.check.botroom_check(ctx.message)

    @commands.cooldown(rate=5, per=20.0, type=commands.BucketType.user)
    @commands.command(aliases=["random", "randint"])
    async def roll(self, ctx, first: int, second: int = 0):
        if first > second:
            first, second = second, first

        option = str(random.randint(first, second))
        await ctx.send(option)
        await self.check.botroom_check(ctx.message)


def setup(bot):
    bot.add_cog(Random(bot))
