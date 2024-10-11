"""
Cog implementing commands using random module.
"""

import random
import shlex

import disnake
from disnake.ext import commands

from cogs.base import Base
from rubbergod import Rubbergod
from utils import cooldowns
from utils.checks import PermissionsCheck

from .messages_cz import MessagesCZ


class Random(Base, commands.Cog):
    def __init__(self, bot: Rubbergod):
        super().__init__()
        self.bot = bot

    @cooldowns.short_cooldown
    @commands.slash_command(name="pick", description=MessagesCZ.pick_brief)
    async def pick(
        self,
        inter: disnake.ApplicationCommandInteraction,
        args: str = commands.Param(max_length=1900, description=MessagesCZ.pick_format),
    ):
        """
        Pick option from given argument.
        Question can be given before options, but must be ended with "?".
        """

        try:
            args_list = shlex.split(args)
        except Exception as e:
            await inter.send(e)
            return

        for i, arg in enumerate(args_list):
            if "?" in arg:
                args_list = args_list[i + 1 :]
                break

        if not args_list:
            await inter.send(MessagesCZ.pick_empty)
            return
        option = disnake.utils.escape_mentions(random.choice(args_list))
        await inter.send(option, ephemeral=PermissionsCheck.is_botroom(inter))

    @cooldowns.short_cooldown
    @commands.slash_command(name="flip", description=MessagesCZ.flip_brief)
    async def flip(self, inter: disnake.ApplicationCommandInteraction):
        await inter.send(random.choice(["True", "False"]), ephemeral=PermissionsCheck.is_botroom(inter))

    @cooldowns.short_cooldown
    @commands.slash_command(name="roll", description=MessagesCZ.rng_generator_format)
    async def roll(self, inter: disnake.ApplicationCommandInteraction, first: int, second: int = 0):
        if first > second:
            first, second = second, first

        option = str(random.randint(first, second))
        await inter.send(option, ephemeral=PermissionsCheck.is_botroom(inter))
