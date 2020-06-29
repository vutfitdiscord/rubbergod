from datetime import date

import discord
from discord.ext import commands

import utils
from config import app_config as config, messages

config = config.Config
messages = messages.Messages


class week(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.cooldown(rate=2, per=20.0, type=commands.BucketType.user)
    @commands.command(aliases=["tyden", "týden", "tyzden", "týždeň"])
    async def week(self, ctx: commands.Context):
        """See if the current week is odd or even"""
        cal_week = date.today().isocalendar()[1]
        stud_week = cal_week - config.starting_week
        even, odd = "sudý", "lichý"
        cal_type = even if cal_week % 2 == 0 else odd
        stud_type = even if stud_week % 2 == 0 else odd

        embed = discord.Embed(title="Týden", color=0xE5DC37)
        embed.set_footer(icon_url=ctx.author.avatar_url, text=str(ctx.author))
        embed.add_field(name="Studijní", value="{} ({})".format(stud_type, stud_week))
        embed.add_field(name="Kalendářní", value="{} ({})".format(cal_type, cal_week))
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(week(bot))
