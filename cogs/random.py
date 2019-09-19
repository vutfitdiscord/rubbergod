from discord.ext import commands

import utils
from cogs import room_check
from logic import roll_dice, rng

# Logic (functionality used by features or rubbergod directly)
roll_dice = roll_dice.Roll()
rng = rng.Rng()


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
        option = rng.pick_option(' '.join(args))
        if option:
            await ctx.send("{} {}".format(option,
                           utils.generate_mention(ctx.author.id)))
        await self.check.botroom_check(ctx.message)

    @commands.cooldown(rate=5, per=20.0, type=commands.BucketType.user)
    @commands.command()
    async def flip(self, ctx):
        await ctx.send(rng.flip())
        await self.check.botroom_check(ctx.message)

    @commands.cooldown(rate=5, per=20.0, type=commands.BucketType.user)
    @commands.command()
    async def roll(self, ctx):
        # TODO: use
        # https://discordpy.readthedocs.io/en/latest/ext/commands/commands.html#basic-converters
        # and only pass integers to the function?
        await ctx.send(rng.generate_number(ctx.message))
        await self.check.botroom_check(ctx.message)


def setup(bot):
    bot.add_cog(Random(bot))
