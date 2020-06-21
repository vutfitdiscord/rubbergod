from datetime import date

import discord
from discord.ext import commands

import utils
from config import config, messages

config = config.Config
messages = messages.Messages


class week(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.cooldown(rate=2, per=20.0, type=commands.BucketType.user)
    @commands.command()
    async def week(self, ctx, *args):
        if args and args[0] == "set":
            if ctx.author.id == config.admin_id:
                config.starting_week = int(args[1])
                await ctx.send(("Starting week set to {}").format(args[1]))

        week = date.today().isocalendar()[1]  # get actual week number
        stud_week = week - config.starting_week
        odd = "Lichý"
        even = "Sudý"
        cal_type = even if week % 2 == 0 else odd
        stud_type = even if stud_week % 2 == 0 else odd
        await ctx.send("Cal\t{}\t{}\nStd\t{}\t{}".format(cal_type, week,
                                                stud_type, stud_week))

def setup(bot):
    bot.add_cog(week(bot))
