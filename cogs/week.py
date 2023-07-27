"""
Cog containing information about week (odd/even) and its relation to calendar/academic week.
"""

from datetime import date

import disnake
from disnake.ext import commands

import utils
from cogs.base import Base
from config import cooldowns
from config.messages import Messages


class Week(Base, commands.Cog):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    @cooldowns.default_cooldown
    @commands.slash_command(name="week", description=Messages.week_brief)
    async def week(self, inter: disnake.ApplicationCommandInteraction):
        """See if the current week is odd or even"""
        cal_week = date.today().isocalendar()[1]
        stud_week = (cal_week - self.config.starting_week) % 52
        even, odd = "sudý", "lichý"
        cal_type = even if cal_week % 2 == 0 else odd

        embed = disnake.Embed(title="Týden", color=0xE5DC37)
        embed.add_field(name="Studijní", value=stud_week)
        embed.add_field(name="Kalendářní", value=f"{cal_type} ({cal_week})")
        embed.add_field(name="Poznámka", value=Messages.week_warning, inline=False)

        utils.add_author_footer(embed, inter.author)

        await inter.response.send_message(embed=embed)


def setup(bot):
    bot.add_cog(Week(bot))
