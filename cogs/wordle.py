import discord
from discord.ext import commands, tasks
from config.app_config import config
from config.messages import Messages as messages
from config import cooldowns
import datetime
import asyncio
import utils
from typing import Tuple, Optional


def get_wordle_solution(forward_days: int = 0) -> Optional[Tuple[int, str]]:
    """
    Returns today's (if forward_days = 0) or other Wordle number and solution
    If forward_days is not 0, returns solution for Wordle #(today + forward_days)
    """
    epoch = datetime.date(2021, 6, 19)  # Wordles start counting from this date
    wanted = datetime.date.today() + datetime.timedelta(days=forward_days)
    wordle_number = (wanted - epoch).days
    if wordle_number < 0 or wordle_number >= len(config.wordle_solutions):
        return None # No solution found
    return wordle_number, config.wordle_solutions[wordle_number]


def seconds_until(hour: int, minute: int) -> int:
    """
    Gets the amount of seconds until a specific time today
    If that time has already passed, returns 0
    """
    now = datetime.datetime.now()
    desired = datetime.datetime.now().replace(hour=hour, minute=minute,
                                              second=0)
    return max((desired - now).total_seconds(), 0)


class Wordle(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.games_channel = None
        self.spoil_job.start()

    def cog_unload(self):
        self.spoil_job.cancel()

    async def get_or_fetch_channel(self):
        self.games_channel = self.bot.get_channel(config.games_room)
        if self.games_channel is None:
            self.games_channel = await self.bot.fetch_channel(config.games_room)

    @tasks.loop(hours=24)
    async def spoil_job(self):
        # Sleeps until 23:55 (by default) or alter in before_loop
        # Then spoils the next day's wordle every 24 hours
        if self.games_channel is None:
            await self.get_or_fetch_channel()
            if self.games_channel is None:
                return
        solution = get_wordle_solution(1)  # tomorrow
        if solution is None:
            self.spoil_job.cancel()
            return
        await self.games_channel.edit(name=f'games-{solution[0]}-{solution[1]}')
        await self.games_channel.send(
            messages.wordle_spoil_tomorrow.format(number=solution[0],
                                                  solution=solution[1]))

    @spoil_job.before_loop
    async def before_spoil_job(self):
        await self.bot.wait_until_ready()
        await asyncio.sleep(
            seconds_until(config.wordle_spoil_hour, config.wordle_spoil_minute))

    @cooldowns.default_cooldown
    @commands.check(utils.helper_plus)
    @commands.command(brief=messages.wordle_spoil_brief)
    async def spoil_wordle(self, ctx: commands.Context):
        # Spoil today's wordle now
        if self.games_channel is None:
            await self.get_or_fetch_channel()
            if self.games_channel is None:
                return
        solution = get_wordle_solution()
        if solution is None:
            await ctx.send(messages.wordle_no_solution)
            return
        await self.games_channel.edit(name=f'games-{solution[0]}-{solution[1]}')
        await self.games_channel.send(
            messages.wordle_spoil_today.format(number=solution[0],
                                               solution=solution[1]))


def setup(bot):
    bot.add_cog(Wordle(bot))
