"""
Cog implementing commands using random module.
"""

import random
import shlex

import disnake
from disnake.ext import commands

from cogs.base import Base
from config import cooldowns
from config.messages import Messages
from permissions import room_check


class Random(Base, commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check = room_check.RoomCheck(bot)

    @cooldowns.short_cooldown
    @commands.slash_command(name="pick", description=Messages.random_pick_brief)
    async def pick(
        self,
        inter: disnake.ApplicationCommandInteraction,
        args: str = commands.Param(max_length=1900, description=Messages.random_pick_format)
    ):
        """
        Pick option from given argument.
        Question can be given before options, but must be ended with "?".
        """

        try:
            args = shlex.split(args)
        except Exception as e:
            await inter.send(e)
            return

        for i, arg in enumerate(args):
            if "?" in arg:
                args = args[i + 1:]
                break

        if not args:
            await inter.send(Messages.random_pick_empty)
            return
        option = disnake.utils.escape_mentions(random.choice(args))
        await inter.send(f"{option} {inter.author.mention}", ephemeral=self.check.botroom_check(inter))

    @cooldowns.short_cooldown
    @commands.slash_command(name="flip", description=Messages.random_flip_brief)
    async def flip(self, inter: disnake.ApplicationCommandInteraction):
        await inter.send(
            random.choice(["True", "False"]),
            ephemeral=self.check.botroom_check(inter)
        )

    @cooldowns.short_cooldown
    @commands.slash_command(name="roll", description=Messages.rng_generator_format)
    async def roll(self, inter: disnake.ApplicationCommandInteraction, first: int, second: int = 0):
        if first > second:
            first, second = second, first

        option = str(random.randint(first, second))
        await inter.send(option, ephemeral=self.check.botroom_check(inter))


def setup(bot):
    bot.add_cog(Random(bot))
