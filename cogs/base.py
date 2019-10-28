import datetime
import traceback

import discord
from discord.ext import commands

import utils
from config import config, messages
from logic import rng
from features import reaction
from repository import karma_repo
from cogs import room_check

rng = rng.Rng()
config = config.Config
messages = messages.Messages
karma_r = karma_repo.KarmaRepository()

boottime = datetime.datetime.now().replace(microsecond=0)


class Base(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.reaction = reaction.Reaction(bot, karma_r)
        self.check = room_check.RoomCheck(bot)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        # The local handlers so far only catch bad arguments so we still
        # want to print the rest
        if isinstance(error, commands.BadArgument) and\
           hasattr(ctx.command, 'on_error'):
            return

        if isinstance(error, commands.CommandNotFound):
            if not ctx.message.content.startswith('!'):
                await ctx.send(messages.no_such_command)
            return
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(messages.spamming.format(
                user=utils.generate_mention(ctx.author.id)
                ))
        else:
            output = 'Ignoring exception in command {}:\n'.format(ctx.command)
            output += ''.join(traceback.format_exception(type(error),
                                                         error,
                                                         error.__traceback__))
            channel = self.bot.get_channel(config.bot_dev_channel)
            print(output)
            output = list(output[0 + i: 1900 + i] for i in range(0, len(output), 1900))
            if channel is not None:
                for message in output:
                    await channel.send("```\n" + message + "\n```")

    @commands.cooldown(rate=2, per=20.0, type=commands.BucketType.user)
    @commands.command()
    async def uptime(self, ctx):
        now = datetime.datetime.now().replace(microsecond=0)
        delta = now - boottime
        await ctx.send(
                messages.uptime_message
                .format(boottime=str(boottime), uptime=str(delta))
                )
    @commands.command()
    async def kachna(self, ctx):
        open_days = config.kachna_open_days
        open_hour = config.kachna_open_hour
        close_hour = config.kachna_close_hour
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
        message = messages.kachna_remaining.format(zustava=str(delta)) if isClosed else messages.kachna_opened
        await ctx.send(message)

    @commands.cooldown(rate=2, per=20.0, type=commands.BucketType.user)
    @commands.command()
    async def week(self, ctx):
        await ctx.send(rng.week())

    @commands.cooldown(rate=2, per=60.0, type=commands.BucketType.user)
    @commands.command()
    async def god(self, ctx):
        embed = self.reaction.make_embed(1)

        channel = await self.check.get_room(ctx.message)
        if channel is not None and channel.id != config.bot_room:
            try:
                msg = await ctx.author.send(embed=embed)
                await ctx.message.delete()
            except discord.errors.Forbidden:
                return
        else:
            msg = await ctx.send(embed=embed)
        await msg.add_reaction("◀")
        await msg.add_reaction("▶")


def setup(bot):
    bot.add_cog(Base(bot))
