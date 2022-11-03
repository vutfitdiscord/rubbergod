import random

import disnake
from disnake.ext import commands

from config import cooldowns
from config.messages import Messages
import shlex


class Random(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @cooldowns.short_cooldown
    @commands.slash_command(name="pick", description=Messages.random_pick_brief)
    async def pick(
        self,
        inter: disnake.ApplicationCommandInteraction,
        args: str = commands.Param(max_length=1900)
    ):
        """"Pick an option"""
        args = shlex.split(args)

        option = disnake.utils.escape_mentions(random.choice(args))
        await inter.send(f"{option} {inter.author.mention}")

    @cooldowns.short_cooldown
    @commands.slash_command(name="flip", description=Messages.random_flip_brief)
    async def flip(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.send_message(random.choice(["True", "False"]))

    @cooldowns.short_cooldown
    @commands.slash_command(name="roll", description=Messages.rng_generator_format)
    async def roll(self, inter: disnake.ApplicationCommandInteraction, first: int, second: int = 0):
        if first > second:
            first, second = second, first

        option = str(random.randint(first, second))
        await inter.response.send_message(option)


def setup(bot):
    bot.add_cog(Random(bot))
