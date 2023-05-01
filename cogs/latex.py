import asyncio
import io
import urllib

import aiohttp
import disnake
from disnake.ext import commands

from cogs.base import Base
from config import cooldowns
from config.messages import Messages

PNG_HEADER = b'\x89PNG\r\n\x1a\n'


class Latex(Base, commands.Cog):
    @cooldowns.default_cooldown
    @commands.command(brief=Messages.latex_desc, description=Messages.latex_help)
    async def latex(self, ctx, *args):
        foreground = "White"

        if len(args) < 1:
            return await ctx.send(f"{Messages.latex_help}\n{Messages.latex_colors}")
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
                            return await ctx.send("Could not get image.")

                        data = await resp.read()
                        if not data.startswith(PNG_HEADER):
                            return await ctx.send("Could not get image.")

                        datastream = io.BytesIO(data)
                        await channel.send(file=disnake.File(datastream, "latex.png"))
                except (asyncio.exceptions.TimeoutError, aiohttp.client_exceptions.ClientConnectorError):
                    await channel.send("Website unreachable")


def setup(bot):
    bot.add_cog(Latex(bot))
