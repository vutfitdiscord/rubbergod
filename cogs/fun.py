"""
Cog containing commands that call random APIs for fun things.
"""

import contextlib
import os
import random
import re
from datetime import datetime
from io import BytesIO
from random import randint
from typing import Dict, List, Optional, Tuple

import aiohttp
import disnake
from disnake.ext import commands

import utils
from cogs.base import Base
from config import cooldowns
from config.messages import Messages
from permissions.custom_errors import ApiError

fuchs_list = os.listdir("images/fuchs/")


class Fun(Base, commands.Cog):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    def custom_footer(self, author, url) -> str:
        return f"📩 {author} | {url} • {datetime.now().strftime('%d.%m.%Y %H:%M')}"

    async def get_image(self, inter, url) -> Optional[Tuple[BytesIO, str]]:
        async with aiohttp.ClientSession() as session:
            # get random image url
            async with session.get(url) as response:
                if response.status != 200:
                    raise ApiError(response.status)
                image = await response.json()

            # get image url
            if isinstance(image, list):
                url = image[0]["url"]
            else:
                url = image.get("url")
                if not url:
                    url = image.get("image")

            # get image bytes
            async with session.get(url) as response:
                if response.status != 200:
                    raise ApiError(response.status)
                file_name = url.split("/")[-1]
                return BytesIO(await response.read()), file_name

    async def get_fact(self, url, key) -> str:
        async with aiohttp.ClientSession() as session:
            with contextlib.suppress(OSError):
                async with session.get(url) as response:
                    if response.status == 200:
                        fact_response_ = await response.json()
                        fact_response = fact_response_[key][0]
        return fact_response

    @cooldowns.default_cooldown
    @commands.slash_command(name="cat", description=Messages.fun_cat_brief)
    async def cat(self, inter):
        """Get random image of a cat"""

        await inter.response.defer()

        image_bytes, file_name = await self.get_image(inter, "https://api.thecatapi.com/v1/images/search")
        image_file = disnake.File(image_bytes, filename=file_name)

        fact_response: str = ""
        if random.randint(0, 9) == 1:
            fact_response = await self.get_fact("https://meowfacts.herokuapp.com/", "data")

        image_embed = disnake.Embed(color=disnake.Color.blue())
        image_embed.set_footer(text=self.custom_footer(inter.author, "thecatapi.com"))
        image_embed.set_image(file=image_file)
        embeds: List[disnake.Embed] = [image_embed]

        if fact_response:
            fact_embed = disnake.Embed(
                title="Cat fact",
                description=fact_response,
                color=disnake.Color.blue(),
            )
            fact_embed.set_footer(text=self.custom_footer(inter.author, "thecatapi.com"))
            embeds.append(fact_embed)

        await inter.send(embeds=embeds)

    @cooldowns.default_cooldown
    @commands.slash_command(name="dog", description=Messages.fun_dog_brief)
    async def dog(self, inter):
        """Get random image of a dog"""

        await inter.response.defer()

        image_bytes, file_name = await self.get_image(inter, "https://api.thedogapi.com/v1/images/search")
        image_file = disnake.File(image_bytes, filename=file_name)

        fact_response: str = ""
        if random.randint(0, 9) == 1:
            fact_response = await self.get_fact("https://dogapi.dog/api/facts/", "facts")

        image_embed = disnake.Embed(color=disnake.Color.blue())
        image_embed.set_footer(text=self.custom_footer(inter.author, "thedogapi.com"))
        image_embed.set_image(file=image_file)
        embeds: List[disnake.Embed] = [image_embed]

        if fact_response:
            fact_embed = disnake.Embed(
                title="Dog fact",
                description=fact_response,
                color=disnake.Color.blue(),
            )
            fact_embed.set_footer(text=self.custom_footer(inter.author, "thedogapi.com"))
            embeds.append(fact_embed)

        await inter.send(embeds=embeds)

    @cooldowns.default_cooldown
    @commands.slash_command(name="fox", description=Messages.fun_fox_brief)
    async def fox(self, inter):
        """Get random image of a fox"""

        await inter.response.defer()

        image_bytes, file_name = await self.get_image(inter, "https://randomfox.ca/floof/")
        image_file = disnake.File(image_bytes, filename=file_name)

        embed = disnake.Embed(color=disnake.Color.blue())
        embed.set_footer(text=self.custom_footer(inter.author, "randomfox.ca"))
        embed.set_image(file=image_file)

        await inter.send(embed=embed)

    @cooldowns.default_cooldown
    @commands.slash_command(name="duck", description=Messages.fun_duck_brief)
    async def duck(self, inter):
        """Get random image of a duck"""

        await inter.response.defer()

        image_bytes, file_name = await self.get_image(inter, "https://random-d.uk/api/v2/random")
        image_file = disnake.File(image_bytes, filename=file_name)

        embed = disnake.Embed(color=disnake.Color.blue())
        embed.set_footer(text=self.custom_footer(inter.author, "random-d.uk"))
        embed.set_image(file=image_file)

        await inter.send(embed=embed)

    @cooldowns.default_cooldown
    @commands.slash_command(name="dadjoke", description=Messages.fun_dadjoke_brief)
    async def dadjoke(self, inter: disnake.ApplicationCommandInteraction, *, keyword=None):
        """Get random dad joke
        Arguments
        ---------
        keyword: search for a certain keyword in a joke
        """

        await inter.response.defer()

        if keyword is not None and ("&" in keyword or "?" in keyword):
            await inter.send("I didn't find a joke like that.")
            return

        params: Dict[str, str] = {"limit": "30"}
        url: str = "https://icanhazdadjoke.com"
        if keyword is not None:
            params["term"] = keyword
            url += "/search"
        headers: Dict[str, str] = {"Accept": "application/json"}

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as response:
                if response.status != 200:
                    raise ApiError(response.status)
                fetched = await response.json()

        if keyword is not None:
            res = fetched["results"]
            if len(res) == 0:
                await inter.send("I didn't find a joke like that.")
                return
            result = random.choice(res)
            result["joke"] = re.sub(
                f"(\\b\\w*{keyword}\\w*\\b)",
                r"**\1**",
                result["joke"],
                flags=re.IGNORECASE,
            )
        else:
            result = fetched

        embed = disnake.Embed(
            title="Dadjoke",
            description=result["joke"],
            color=disnake.Color.blue(),
            url="https://icanhazdadjoke.com/j/" + result["id"],
        )
        embed.set_footer(text=self.custom_footer(inter.author, "icanhazdadjoke.com"))

        await inter.send(embed=embed)

    @cooldowns.default_cooldown
    @commands.slash_command(name="yo_mamajoke", description=Messages.fun_yo_mamajoke_brief)
    async def yo_mamajoke(self, inter):
        """Get random Yo momma joke"""

        await inter.response.defer()

        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.yomomma.info/") as response:
                if response.status != 200:
                    raise ApiError(response.status)
                result = await response.json()

        embed = disnake.Embed(
            title="Yo mamajoke",
            description=result["joke"],
            color=disnake.Color.blue(),
            url="https://yomomma.info",
        )
        embed.set_footer(text=self.custom_footer(inter.author, "yomomma.info"))

        await inter.send(embed=embed)

    @cooldowns.default_cooldown
    @commands.slash_command(name="fuchs", description=Messages.fun_fuchs_brief)
    async def fuchs(self, inter, hlaskaid: int = commands.Param(default=None, ge=1, le=len(fuchs_list))):

        await inter.response.defer()

        if len(fuchs_list) == 0:
            inter.send(Messages.fun_fuchs_no_reaction)
            return

        if hlaskaid is None:
            index = randint(1, len(fuchs_list))
        else:
            index = hlaskaid

        embed = disnake.Embed(
            title="Fuchs reakce",
            color=disnake.Color.blue(),
        )
        embed.set_image(url=f"attachment://{str(index)}.png")

        utils.add_author_footer(embed, inter.author, additional_text=[f" (hláškaid: #{str(index)})"])

        with open("images/fuchs/" + str(index) + ".png", 'rb') as fp:
            await inter.send(embed=embed, file=disnake.File(fp=fp, filename=str(index) + ".png"))


def setup(bot):
    bot.add_cog(Fun(bot))
