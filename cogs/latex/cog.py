"""
Cog for interpreting latex commands as images.
"""

import asyncio
import io
import urllib

import aiohttp
import disnake
from disnake.ext import commands

from cogs.base import Base
from config import cooldowns
from rubbergod import Rubbergod

from .messages_cz import MessagesCZ

PNG_HEADER = b"\x89PNG\r\n\x1a\n"


class Latex(Base, commands.Cog):
    def __init__(self, bot: Rubbergod):
        super().__init__()
        self.bot = bot

    @cooldowns.default_cooldown
    @commands.command(brief=MessagesCZ.latex_desc, description=MessagesCZ.latex_help)
    async def latex(self, ctx: commands.Context, *args):
        foreground = "White"

        if len(args) < 1:
            await ctx.send(f"{MessagesCZ.latex_help}\n{MessagesCZ.latex_colors}")
            return
        if "?fg=" in args[0]:
            foreground = args[0][4:]
            args = args[1:]

        eq = " ".join(args)
        channel = ctx.channel
        async with ctx.typing():
            eq = urllib.parse.quote(eq)
            imgURL = f"http://www.sciweavers.org/tex2img.php?eq={eq}&fc={foreground}&im=png&fs=25&edit=0"

            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                try:
                    async with session.get(imgURL) as resp:
                        if resp.status != 200:
                            await ctx.send("Could not get image.")
                            return

                        data = await resp.read()
                        if not data.startswith(PNG_HEADER):
                            await ctx.send("Could not get image.")
                            return

                        datastream = io.BytesIO(data)
                        await channel.send(file=disnake.File(datastream, "latex.png"))
                except (asyncio.exceptions.TimeoutError, aiohttp.client_exceptions.ClientConnectorError):
                    await channel.send("Website unreachable")
