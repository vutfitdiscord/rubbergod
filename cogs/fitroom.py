"""
Cog for finding rooms on FIT BUT.
"""

from io import BytesIO

import disnake
import requests
from bs4 import BeautifulSoup
from cairosvg import svg2png
from disnake.ext import commands

import utils
from cogs.base import Base
from config import cooldowns
from config.messages import Messages


class FitRoom(Base, commands.Cog):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    @cooldowns.default_cooldown
    @commands.slash_command(name="room", description=Messages.fit_room_brief)
    async def room(
        self,
        inter: disnake.ApplicationCommandInteraction,
        room: str
    ):
        await inter.response.defer()
        url = f"https://www.fit.vut.cz/fit/map/.cs?show={room.upper()}&big=1"
        r = requests.get(url)
        if r.status_code != 200:
            await inter.edit_original_response(Messages.fit_room_unreach)
            return

        try:
            soup = BeautifulSoup(r.content, 'html.parser')
            main_body = soup.find("main", {"id": "main"})
            floor_list = main_body.find("ul", {"class": "pagination__list"})
            active_floor = floor_list.find("a", {"aria-current": "page"})
            image = main_body.find("svg", {"id": "map"})
            cursor = main_body.find("polygon", {"id": "arrow"})
        except AttributeError:
            await inter.edit_original_response(Messages.fit_room_parsing_failed)
            return

        if image is None or cursor is None:
            await inter.edit_original_response(
                Messages.fit_room_room_not_on_plan(room=room[:1024])
            )
            return

        image_bytes = BytesIO()
        image_bytestring = str(image).encode("utf-8")
        svg2png(bytestring=image_bytestring, write_to=image_bytes, parent_width=720,
                parent_height=1000, background_color="white", dpi=300)
        image_bytes.seek(0)

        embed = disnake.Embed(
            title=f"Místnost: {room.upper()}",
            url=f"https://www.fit.vut.cz/fit/room/{room.upper()}/.cs",
            color=disnake.Color.dark_blue()
        )
        embed.set_image(url="attachment://plan.png")
        embed.description = f"[Odkaz na plánek]({url})"
        utils.add_author_footer(embed, inter.author, additional_text=[str(active_floor.text)])
        file = disnake.File(fp=image_bytes, filename="plan.png")
        await inter.edit_original_response(embed=embed, file=file)


def setup(bot):
    bot.add_cog(FitRoom(bot))
