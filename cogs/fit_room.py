import discord
from discord.ext import commands
import requests
from bs4 import BeautifulSoup
from cairosvg import svg2png
from io import BytesIO
import utils
from config import cooldowns
from config.messages import Messages


class FitRoom(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @cooldowns.default_cooldown
    @commands.command(brief=Messages.fit_room_brief, description=Messages.fit_room_help)
    async def room(self, ctx: commands.Context, *, room: str):
        url = f"https://www.fit.vut.cz/fit/map/.cs?show={room.upper()}&big=1"
        r = requests.get(url)
        if r.status_code != 200:
            return await ctx.send(Messages.fit_room_unreach)

        async with ctx.typing():
            try:
                soup = BeautifulSoup(r.content, 'html.parser')
                main_body = soup.find("main", {"id": "main"})
                floor_list = main_body.find("ul", {"class": "pagination__list"})
                active_floor = floor_list.find("a", {"aria-current": "page"})
                image = main_body.find("svg")
                overlay = image.find("g", {"id": "layer3"})
                cursor = overlay.find("polygon",
                                      {"style": "fill:red;stroke:none;pointer-events:none"})
            except:
                return await ctx.send(Messages.fit_room_parsing_failed)

            if image is None or cursor is None:
                if len(room) >= 2:
                    url = f"https://www.fit.vut.cz/fit/map/{room[1]}/.cs?show={room.upper()}&big=1"
                    r = requests.get(url)
                    if r.status_code != 200:
                        return await ctx.send(Messages.fit_room_unreach)

                    try:
                        soup = BeautifulSoup(r.content, 'html.parser')
                        main_body = soup.find("main", {"id": "main"})
                        floor_list = main_body.find("ul", {"class": "pagination__list"})
                        active_floor = floor_list.find("a", {"aria-current": "page"})
                        image = main_body.find("svg")
                        overlay = image.find("g", {"id": "layer3"})
                        cursor = overlay.find("polygon", {
                            "style": "fill:red;stroke:none;pointer-events:none"})
                    except:
                        return await ctx.send(Messages.fit_room_parsing_failed)

                    if image is None or cursor is None:
                        return await ctx.send(
                            utils.fill_message("fit_room_room_not_on_plan", room=room))
                else:
                    return await ctx.send(
                        utils.fill_message("fit_room_room_not_on_plan", room=room))

            image_bytes = BytesIO()
            svg2png(bytestring=str(image).encode("utf-8"), write_to=image_bytes, parent_width=720,
                    parent_height=1000, background_color="white", dpi=300)
            image_bytes.seek(0)

            embed = discord.Embed(title=f"Místnost: {room}", color=discord.Color.dark_blue())
            embed.set_image(url="attachment://plan.png")
            embed.description = f"[Odkaz na plánek]({url})"
            utils.add_author_footer(embed, ctx.author, additional_text=[str(active_floor.text)])
            file = discord.File(fp=image_bytes, filename="plan.png")
            await ctx.send(embed=embed, file=file)


def setup(bot):
    bot.add_cog(FitRoom(bot))
