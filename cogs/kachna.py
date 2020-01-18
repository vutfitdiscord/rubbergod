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
        open_days = config.kachna_open_days
        open_hour = config.kachna_open_hour
        close_hour = config.kachna_close_hour
        temp_closed = config.kachna_temp_closed

        def next_weekday(d, weekday):
            days_ahead = weekday - d.weekday()
            if days_ahead < 0:
                days_ahead += 7
            if days_ahead == 0 and d.hour >= close_hour:
                days_ahead += 7
            return d + datetime.timedelta(days_ahead)

        now = datetime.datetime.now().replace(microsecond=0)
        open_date = next_weekday(now, open_days[0])
        for open_day in open_days:
            current_open_date = next_weekday(now, open_day)
            if current_open_date <= open_date:
                open_date = current_open_date
        opentime = open_date.replace(hour=open_hour, minute=0, second=0)
        isClosed = (now < opentime) or (opentime.replace(hour=close_hour) < now)
        delta = opentime - now
        message = (
            messages.kachna_remaining.format(zbyva=str(delta))
            if isClosed
            else messages.kachna_opened
        )
        if temp_closed:
            message = messages.kachna_temp_closed
        await ctx.send(message)

    @commands.command()
    async def kachna_switch(self, ctx):
        message = messages.insufficient_rights.format(
            user=utils.generate_mention(ctx.author.id)
        )
        if ctx.author.id == config.admin_id:
            if config.kachna_temp_closed == False:
                config.kachna_temp_closed = True
                message = messages.kachna_switched.format(
                    open_closed="zavřená dlouhodobě"
                )
            else:
                config.kachna_temp_closed = False
                message = messages.kachna_switched.format(
                    open_closed="otevřená pravidelně"
                )
        await ctx.send(message)


def setup(bot):
    bot.add_cog(Kachna(bot))
