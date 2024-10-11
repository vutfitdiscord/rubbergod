"""
Cog implementing information about office hours of the study department.
"""

import asyncio

import aiohttp
import disnake
from disnake.ext import commands
from lxml import etree

from cogs.base import Base
from rubbergod import Rubbergod
from utils.embed import add_author_footer
from utils.errors import ApiError

from .messages_cz import MessagesCZ


class Studijni(Base, commands.Cog):
    def __init__(self, bot: Rubbergod):
        super().__init__()
        self.bot = bot

    @commands.slash_command(name="studijni", description=MessagesCZ.studijni_brief)
    async def studijni(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer()
        url = "https://www.fit.vut.cz/fit/room/C109/.cs"
        try:
            async with self.bot.rubbergod_session.get(url) as response:
                html = await response.text()
        except (aiohttp.ClientConnectionError, asyncio.TimeoutError) as error:
            raise ApiError(str(error))

        htmlparser = etree.HTMLParser()
        xDoc2 = etree.fromstring(html, htmlparser)
        hours_div = xDoc2.xpath("//*[b[contains(text(),'Úřední hodiny')]]//following-sibling::div")
        embed = disnake.Embed(title=MessagesCZ.studijni_title, url=url, color=disnake.Color.blue())
        if hours_div:
            hours = etree.tostring(hours_div[0], encoding=str, method="text")
            additional_info = xDoc2.xpath("//main//section/p")
            if additional_info:
                info = etree.tostring(additional_info[0], encoding=str, method="text").split(":", 1)
                if len(info) > 1:
                    embed.add_field(name=info[0], value=info[1], inline=False)
        else:
            hours_div = xDoc2.xpath("//main//section")
            if len(hours_div):
                hours = "".join(hours_div[0].itertext())
                hours = hours.strip()
            else:
                hours = MessagesCZ.web_error
        embed.add_field(name=MessagesCZ.office_hours, value=hours, inline=False)
        add_author_footer(embed, inter.author)
        await inter.edit_original_response(embed=embed)
