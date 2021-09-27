from datetime import date

import discord
from discord.ext import commands

import utils
from config import app_config as config, messages, cooldowns

config = config.Config
messages = messages.Messages


class week(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @cooldowns.default_cooldown
    @commands.command(aliases=["tyden", "týden", "tyzden", "týždeň"], brief=messages.week_brief)
    async def week(self, ctx: commands.Context):
        """See if the current week is odd or even"""
        cal_week = date.today().isocalendar()[1]
        stud_week = cal_week - config.starting_week
        even, odd = "sudý", "lichý"
        cal_type = even if cal_week % 2 == 0 else odd

        embed = discord.Embed(title="Týden", color=0xE5DC37)
        embed.add_field(name="Studijní", value=stud_week)
        embed.add_field(name="Kalendářní", value=f"{cal_type} ({cal_week})")
        embed.add_field(name="Poznámka", value=messages.week_warning, inline=False)

        utils.add_author_footer(embed, ctx.author)

        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(week(bot))
