"""
Cog for interpreting latex commands as images.
"""

import asyncio
import io
import re

import aiohttp
import disnake
from disnake.ext import commands

from cogs.base import Base
from rubbergod import Rubbergod
from utils import cooldowns, errors

from .messages_cz import MessagesCZ


class Latex(Base, commands.Cog):
    def __init__(self, bot: Rubbergod):
        super().__init__()
        self.bot = bot

    async def get_image_url(self, text: str) -> str:
        """Extract the image URL from the response text."""
        pattern = r"/upload/Tex2Img_\w+\/\w+\.png"
        matches = re.findall(pattern, text)
        return matches[0]

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
            baseURL = "https://www.sciweavers.org/"
            data = {
                "eq_latex": eq,
                "eq_forecolor": foreground,
                "eq_bkcolor": "Transparent",
                "eq_font_family": "arev",
                "eq_font": "12",
                "eq_imformat": "PNG",
            }
            # Send request to create image
            try:
                async with self.bot.rubbergod_session.post(
                    baseURL + "process_form_tex2img", data=data
                ) as resp:
                    if resp.status != 200:
                        raise errors.ApiError(MessagesCZ.api_error(resp.status))

                    text = await resp.text()
                    image_url = await self.get_image_url(text)
                    if not image_url:
                        await ctx.send(MessagesCZ.image_error)
                        return
            except (aiohttp.ClientConnectorError, asyncio.TimeoutError) as error:
                raise errors.ApiError(str(error))

            # Download image
            try:
                async with self.bot.rubbergod_session.get(baseURL + image_url) as resp:
                    datastream = io.BytesIO(await resp.read())
            except (aiohttp.ClientConnectorError, asyncio.TimeoutError) as error:
                raise errors.ApiError(str(error))

            await channel.send(file=disnake.File(datastream, "latex.png"))
